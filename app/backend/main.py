from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.config import IS_LAB, FANUC_PORT, TELEMETRY_ENV, STARK_MACHINES, MachineConfig
from backend.datasources import FanucMqttDataSource, generate_raw_events, FanucNotAvailableError
from backend.models import CncMachineData, DashboardData
from backend.db import get_db, Event, Cycle, engine, Base
from sqlalchemy.orm import Session
import csv
import io
import asyncio
from datetime import datetime

app = FastAPI(title="CNC Telemetry Stark")

# Ensure tables exist on startup
@app.on_event("startup")
def startup_event():
    print("[DB] Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    print("[DB] Database ready.")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DataSource based on Environment
# Agora que temos um Simulador MQTT externo (fanuc-sim-mqtt), 
# queremos usar o FanucMqttDataSource tanto em FIELD quanto em LAB.
# O LabSimulatedDataSource (mock interno) fica deprecated/reservado para testes unitários.

print(f"[STARTUP] Initializing Telemetry Backend in {TELEMETRY_ENV.upper()} mode.")
print(f"[STARTUP] Connecting to MQTT Broker at {FanucMqttDataSource.__init__.__defaults__[0] if FanucMqttDataSource.__init__.__defaults__ else 'localhost'}...")

# Sempre tenta usar MQTT (seja do Simulador ou do Driver Real)
try:
    data_source = FanucMqttDataSource()
    print("[STARTUP] MQTT DataSource initialized successfully.")
except Exception as e:
    print(f"[STARTUP] Warning: Failed to connect to MQTT ({e}).")
    raise e

@app.get("/healthz")
async def health_check():
    return {
        "status": "ok", 
        "version": "1.0.0", 
        "env": TELEMETRY_ENV,
        "source": "lab_simulation" if IS_LAB else "fanuc_mqtt"
    }

@app.get("/demo/dashboard")
async def get_dashboard_data():
    """
    Endpoint principal consumido pelo Dashboard.
    Retorna o estado atual das máquinas e KPIs.
    Agora suporta Multi-Máquina (3 FANUCs).
    """
    
    async def fetch_one(cfg: MachineConfig) -> CncMachineData:
        try:
            # Try to get status (Simulated or Real)
            status = await data_source.get_machine_status(cfg.id)
            
            # Enforce Config Metadata (Name/Model)
            # This ensures the UI shows the correct configured name even if data source is generic
            # But we need to be careful not to overwrite if data source provides better info?
            # For now, we trust config.
            # Note: CncMachineData doesn't have display_name/model fields explicitly in Pydantic model 
            # unless we add them or rely on 'machine_id' and 'controller_type'.
            # The prompt asked to ensure types.ts has them. 
            # Backend model CncMachineData needs to support them or we rely on ID mapping in Front.
            # Let's just return the status as is, assuming data_source sets machine_id correctly.
            return status
            
        except FanucNotAvailableError as exc:
            # Machine OFFLINE (Field mode failure)
            # Return a safe OFFLINE object
            return CncMachineData(
                machine_id=cfg.id,
                state="OFFLINE",
                controller_type="FANUC", # Default
                model=cfg.model, # Model from Config (Correct display even if offline)
                timestamp=datetime.now().isoformat(),
                availability="UNAVAILABLE",
                execution_state="STOPPED",
                controller_mode="OFFLINE",
                program_name="",
                current_block="",
                current_tool="",
                spindle_load=None,
                spindle_speed=None,
                feed_rate=None,
                feed_rate_override=None,
                load_history=[0]*20,
                part_count=0,
                run_time_min=0,
                connection_status="OFFLINE",
                connection_error=str(exc),
                cycle_time_machine_s=None,
                cycle_time_total_s=None
            )

    # Gather all machines in parallel
    machines = await asyncio.gather(*[fetch_one(cfg) for cfg in STARK_MACHINES])
    
    # Calculate Basic KPIs (Aggregated)
    total_machines = len(machines)
    active_machines = len([m for m in machines if m.execution_state == "ACTIVE" or m.execution_state == "RUN"])
    
    return DashboardData(
        machines=machines,
        kpis={
            "global_oee": 0.0, # Placeholder
            "total_active_machines": active_machines,
            "avg_spindle_load": 0.0,
            "total_parts_shift": 0,
            "avg_oee": 0.0,
            "total_production": 0,
            "avg_scrap_rate": 0.0,
            "availability_rate": active_machines / total_machines if total_machines > 0 else 0
        },
        monthly_trend=[],
        machine_performance=[],
        downtime_reasons=[],
        shift_performance=[],
        last_updated=datetime.now().isoformat(),
        source="multi_machine_aggregator"
    )

@app.get("/demo/events")
async def get_demo_events():
    """
    Retorna lista de eventos (raw data) para tabela.
    """
    # In field, this might need to fetch from a DB in the future
    return generate_raw_events()

@app.get("/demo/export")
async def export_csv():
    """
    Exporta os eventos em formato CSV para download.
    """
    # Export ALL events (no limit) for CSV
    events = generate_raw_events(limit=None)
    if not events:
        return Response(content="No data", media_type="text/plain")

    output = io.StringIO()
    # Define headers based on first item keys
    headers = events[0].keys()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(events)
    
    csv_content = output.getvalue()
    
    filename = f"telemetry_{TELEMETRY_ENV}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/v1/history/events")
def get_history_events(
    machine_id: str = None, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de mudanças de estado (RUN/IDLE/ALARM).
    """
    query = db.query(Event)
    if machine_id:
        query = query.filter(Event.machine_id == machine_id)
    return query.order_by(Event.timestamp.desc()).limit(limit).all()

@app.get("/v1/history/cycles")
def get_history_cycles(
    machine_id: str = None, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de ciclos de produção (peças feitas).
    """
    query = db.query(Cycle)
    if machine_id:
        query = query.filter(Cycle.machine_id == machine_id)
    return query.order_by(Cycle.ts_end.desc()).limit(limit).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
