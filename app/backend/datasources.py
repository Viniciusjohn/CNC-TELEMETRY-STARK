import httpx
import paho.mqtt.client as mqtt
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Protocol
from backend.models import CncMachineData, DashboardData, TelemetrySample
from backend.config import FANUC_PORT, STARK_MACHINES_BY_ID, FANUC_DRIVER_BASE_URL, MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_TOPIC_PREFIX
from backend.cycles import cycle_tracker
from backend.adapters import FanucAdapter

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FanucNotAvailableError(Exception):
    pass

class MachineDataSource(Protocol):
    async def get_dashboard_data(self) -> DashboardData: ...
    async def get_machine_status(self, machine_id: str) -> CncMachineData: ...

class FanucMqttDataSource:

    def __init__(self, host: str = MQTT_BROKER_HOST, port: int = MQTT_BROKER_PORT):
        self.host = host
        self.port = port
        self.adapters: Dict[str, FanucAdapter] = {}
        self.last_seen: Dict[str, datetime] = {}
        
        # Initialize Adapters for configured machines
        for m_id in STARK_MACHINES_BY_ID.keys():
            self.adapters[m_id] = FanucAdapter(m_id)
        
        # Initialize MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Start Background Loop
        try:
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            logger.info(f"[MQTT] Connected to broker at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to connect: {e}")

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"[MQTT] Connected with result code {rc}")
        # Subscribe to all fanuc topics: fanuc/+/+
        topic = f"{MQTT_TOPIC_PREFIX}/#"
        client.subscribe(topic)
        logger.info(f"[MQTT] Subscribed to {topic}")

    def on_message(self, client, userdata, msg):
        try:
            # Topic format: fanuc/{machine_id}/{veneer}
            # Ex: fanuc/STARK_TORNO_PILOTO/StateData
            parts = msg.topic.split('/')
            if len(parts) < 3:
                return
            
            machine_id = parts[1]
            veneer_name = parts[2]

            # Log controlado do payload bruto para debug de integração com o driver
            # (útil para alinhar FanucAdapter ao formato REAL do Ladder99)
            # Os tópicos reais observados são: state, production, spindle, alarms
            if machine_id == "STARK_TORNO_PILOTO" and veneer_name in ("state", "production", "spindle", "alarms"):
                try:
                    raw_payload = msg.payload.decode(errors="ignore")
                except Exception:
                    raw_payload = str(msg.payload)
                logger.info(f"[MQTT RAW] topic={msg.topic} payload={raw_payload}")
            
            if machine_id not in self.adapters:
                # Auto-register unknown machine? Better to stick to config rule.
                # If we allow unknown, we might leak junk data.
                if machine_id in STARK_MACHINES_BY_ID:
                    self.adapters[machine_id] = FanucAdapter(machine_id)
                else:
                    return # Ignore unknown machines
            
            payload = msg.payload.decode()
            adapter = self.adapters[machine_id]
            
            # Ingest data into adapter
            sample = adapter.ingest(veneer_name, payload)
            
            # Update liveness
            self.last_seen[machine_id] = datetime.now()
            
            # Update Cycle Tracker (centralized logic)
            # We use the canonical state from the sample
            cycle_tracker.update(
                machine_id=machine_id,
                now=datetime.now(),
                state=sample.state,
                part_count=sample.part_count
            )
                
        except Exception as e:
            logger.error(f"[MQTT] Error processing message {msg.topic}: {e}")

    async def get_machine_status(self, machine_id: str) -> CncMachineData:
        if machine_id not in STARK_MACHINES_BY_ID:
             raise FanucNotAvailableError(f"Unknown machine ID: {machine_id}")
        
        # Check Staleness (e.g., no data for 30 seconds)
        if machine_id not in self.last_seen:
            raise FanucNotAvailableError(f"No data received for {machine_id} (Waiting for MQTT)")
            
        delta = datetime.now() - self.last_seen[machine_id]
        if delta.total_seconds() > 30:
            raise FanucNotAvailableError(f"Connection lost (Last seen {int(delta.total_seconds())}s ago)")

        # Get latest sample from adapter
        if machine_id not in self.adapters:
             self.adapters[machine_id] = FanucAdapter(machine_id)
             
        sample = self.adapters[machine_id].to_sample()
        
        # Map canonical state to UI-specific fields
        ui_exec_state = "STOPPED"
        if sample.state == "RUN": ui_exec_state = "ACTIVE"
        elif sample.state == "IDLE": ui_exec_state = "READY"
        elif sample.state == "ALARM": ui_exec_state = "STOPPED"
        
        # Enrich with Cycle Tracker Data (computed externally)
        tracker_state = cycle_tracker.get_state(machine_id)

        # Start from adapter sample dict and override cycle fields if tracker has better data
        sample_data = sample.dict()
        if tracker_state:
            if tracker_state.last_cycle_machine_s is not None:
                sample_data["cycle_time_machine_s"] = tracker_state.last_cycle_machine_s
            if tracker_state.last_cycle_total_s is not None:
                sample_data["cycle_time_total_s"] = tracker_state.last_cycle_total_s
        
        # Build full CncMachineData
        config = STARK_MACHINES_BY_ID.get(machine_id)
        model_name = config.model if config else "FANUC Generic"

        return CncMachineData(
            **sample_data,
            controller_type="FANUC",
            model=model_name,
            availability="AVAILABLE",
            execution_state=ui_exec_state,
            connection_status="ONLINE",
            
            # History (TODO: Implement real history buffer in adapter or redis)
            load_history=[sample.spindle_load or 0.0] * 20,
            run_time_min=0, # TODO: Calc from cycle tracker
        )

    async def get_dashboard_data(self) -> DashboardData:
        machines_data = []
        
        # Iterate over configured machines
        for m_id in STARK_MACHINES_BY_ID.keys():
            try:
                # Get status from self (uses adapter cache)
                m_data = await self.get_machine_status(m_id)
                machines_data.append(m_data)
            except FanucNotAvailableError:
                # If machine is configured but no data yet, return offline placeholder
                # This ensures the card appears in UI even if offline
                machines_data.append(CncMachineData(
                    machine_id=m_id,
                    timestamp=datetime.now().isoformat(),
                    state="OFFLINE",
                    execution_state="STOPPED",
                    availability="UNAVAILABLE",
                    controller_type="FANUC",
                    connection_status="OFFLINE",
                    part_count=0
                ))
            except Exception as e:
                logger.error(f"Error getting status for {m_id}: {e}")
        
        # Calculate Global KPIs
        total_parts = sum(m.part_count for m in machines_data)
        active_count = sum(1 for m in machines_data if m.execution_state == "ACTIVE")
        total_machines = len(machines_data)
        global_oee = active_count / total_machines if total_machines > 0 else 0.0

        return DashboardData(
            machines=machines_data,
            kpis={
                "total_production": total_parts,
                "global_oee": global_oee,
                "active_machines": active_count
            },
            monthly_trend=[],
            machine_performance=[],
            downtime_reasons=[],
            shift_performance=[],
            last_updated=datetime.now().isoformat(),
            source="field_mqtt"
        )

# Legacy HTTP Source (Kept for reference or fallback if configured)
class FanucDataSource:
    def __init__(self, port: int):
        self.port = port

    async def get_machine_status(self, machine_id: str) -> CncMachineData:
        # Lookup Machine Config
        if machine_id not in STARK_MACHINES_BY_ID:
             raise FanucNotAvailableError(f"Unknown machine ID: {machine_id}")
        
        cfg = STARK_MACHINES_BY_ID[machine_id]
        
        # Real Integration with fanuc-driver via HTTP
        # URL Example: http://localhost:9001/machines/STARK_TORNO_PILOTO
        url = f"{FANUC_DRIVER_BASE_URL}/machines/{machine_id}"
        
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                # Expected JSON format from driver (generic assumption based on prompt):
                # {
                #   "status": "RUN" | "IDLE" | "ALARM",
                #   "rpm": 1200,
                #   "feed": 100,
                #   "part_count": 150,
                #   "program": "O1234",
                #   "tool": "T01"
                # }
                
                raw_state = data.get("status", "IDLE").upper()
                part_count = int(data.get("part_count", 0))
                
                # Normalize State for UI
                # Map driver state to CncMachineData execution_state
                # Assuming driver returns simple "RUN", "IDLE", "ALARM"
                normalized_state = raw_state
                if normalized_state not in ["ACTIVE", "READY", "STOPPED", "FEED_HOLD", "RUN", "IDLE", "ALARM"]:
                     normalized_state = "STOPPED" # Fallback
                
                # Fix for UI: UI expects specific ExecutionState enum values?
                # Types.ts: 'ACTIVE' | 'READY' | 'STOPPED' | 'INTERRUPTED' | 'FEED_HOLD'
                # Map RUN -> ACTIVE, IDLE -> READY/STOPPED
                ui_state = normalized_state
                if normalized_state == "RUN": ui_state = "ACTIVE"
                elif normalized_state == "IDLE": ui_state = "READY"
                elif normalized_state == "ALARM": ui_state = "STOPPED"

                # Update Cycle Tracker
                now = datetime.now()
                tracker_state = cycle_tracker.update(
                   machine_id=machine_id,
                   now=now,
                   state=normalized_state, # Use raw-ish state for logic if needed, or mapped
                   part_count=part_count
                )

                return CncMachineData(
                   machine_id=machine_id,
                   controller_type="FANUC",
                   timestamp=now.isoformat(),
                   availability="AVAILABLE",
                   execution_state=ui_state,
                   controller_mode="MEM", # TODO: Read from driver if available
                   program_name=str(data.get("program", "")),
                   current_block=str(data.get("block", "")),
                   current_tool=str(data.get("tool", "")),
                   
                   spindle_load=float(data.get("load", 0)),
                   spindle_speed=float(data.get("rpm", 0)),
                   feed_rate=float(data.get("feed", 0)),
                   feed_rate_override=100, # Default
                   
                   load_history=[0]*20, # Driver might not provide history yet
                   part_count=part_count,
                   run_time_min=0, # TODO: Calc
                   
                   connection_status="ONLINE",
                   connection_error=None,
                   
                   cycle_time_machine_s=tracker_state.last_cycle_machine_s,
                   cycle_time_total_s=tracker_state.last_cycle_total_s
                )

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            # Log error (print for now, use logger in prod)
            print(f"[FanucDataSource] Connection failed for {machine_id} at {url}: {e}")
            raise FanucNotAvailableError(f"Driver unavailable at {url}: {str(e)}")

    async def get_dashboard_data(self) -> DashboardData:
        # This method might not be used if main.py orchestrates the loop, 
        # but we keep it for compatibility or simpler single-call usage.
        # However, based on prompt, main.py will gather.
        return DashboardData(
            machines=[],
            kpis={},
            monthly_trend=[],
            machine_performance=[],
            downtime_reasons=[],
            shift_performance=[],
            last_updated=datetime.now().isoformat(),
            source="field_fanuc"
        )

from backend.db import SessionLocal, Event, Cycle
from sqlalchemy import desc

def generate_raw_events(count=100):
    """
    Retorna lista de eventos REAIS do banco de dados (Eventos de Estado + Ciclos de Produção).
    
    CRITICAL DATA CONTRACT (PT-BR):
    Esta função retorna dicionários com chaves em PORTUGUÊS que são consumidas diretamente 
    pelo Frontend (App.tsx / TelemetryEventRow).
    
    Não altere as chaves abaixo sem atualizar app/types.ts -> TelemetryEventRow.
    
    Chaves esperadas:
    - id, data, maquina_id, produto, turno
    - tempo_ciclo_min, pecas_boas, pecas_refugo
    - parada_min, motivo_parada
    """
    db = SessionLocal()
    try:
        # Fetch last events and cycles
        events_db = db.query(Event).order_by(desc(Event.timestamp)).limit(count).all()
        cycles_db = db.query(Cycle).order_by(desc(Cycle.ts_end)).limit(count).all()
        
        combined = []
        
        # Process Events
        for e in events_db:
            combined.append({
                "timestamp_obj": e.timestamp,
                "timestamp": e.timestamp.isoformat(),
                "machine_id": e.machine_id,
                "state": e.new_state,
                "rpm": 0,
                "program": "N/A",
                "product": "N/A",
                "shift": "1" if 6 <= e.timestamp.hour < 14 else ("2" if 14 <= e.timestamp.hour < 22 else "3"),
                "cycle_time_machine_s": 0,
                "cycle_time_total_s": 0,
                "cycle_time_min": 0,
                "good_parts": 0,
                "scrap_parts": 0,
                "stop_min": 0,
                "stop_reason": e.reason or f"State: {e.new_state}"
            })
            
        # Process Cycles
        for c in cycles_db:
            combined.append({
                "timestamp_obj": c.ts_end,
                "timestamp": c.ts_end.isoformat(),
                "machine_id": c.machine_id,
                "state": "RUN",
                "rpm": 0, # Média não persistida ainda
                "program": c.program_name or "Unknown",
                "product": c.program_name or "Unknown", # Use Program as Product for now
                "shift": "1" if 6 <= c.ts_end.hour < 14 else ("2" if 14 <= c.ts_end.hour < 22 else "3"),
                "cycle_time_machine_s": c.duration_s,
                "cycle_time_total_s": c.duration_s, # Approx
                "tempo_ciclo_min": round(c.duration_s / 60.0, 2), # Campo esperado pelo frontend (pt-br keys?)
                # O frontend usa chaves em ingles ou portugues?
                # App.tsx: row.tempo_ciclo_min, row.pecas_boas, row.pecas_refugo, row.motivo_parada
                # Ah! O App.tsx usa chaves em PORTUGUÊS na tabela!
                # Vou mapear para ambos para garantir.
                
                "good_parts": 1,
                "scrap_parts": 0,
                "stop_min": 0,
                "stop_reason": "Cycle Complete"
            })

        # Sort combined list by timestamp desc
        combined.sort(key=lambda x: x["timestamp_obj"], reverse=True)
        
        # Trim to requested count
        final_list = combined[:limit] if limit else combined
        
        # Clean up obj before sending
        output = []
        for item in final_list:
            # Map to frontend expected keys (App.tsx lines 467+)
            # keys: data (timestamp?), maquina_id, produto, turno, tempo_ciclo_min, pecas_boas, pecas_refugo, parada_min, motivo_parada
            
            # Mapping
            mapped = {
                "id": str(item["timestamp_obj"]), # Fake ID for key
                "data": item["timestamp"],
                "maquina_id": item["machine_id"],
                "produto": item["product"],
                "turno": f"Turno {item['shift']}",
                "tempo_ciclo_min": item.get("tempo_ciclo_min", 0),
                "pecas_boas": item["good_parts"],
                "pecas_refugo": item["scrap_parts"],
                "parada_min": item["stop_min"],
                "motivo_parada": item["stop_reason"]
            }
            output.append(mapped)
            
        return output
        
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        return []
    finally:
        db.close()
