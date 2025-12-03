from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from backend.simulation import get_simulated_data, generate_raw_events
import csv
import io
from datetime import datetime

app = FastAPI(title="CNC Telemetry Demo")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for demo simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/demo/dashboard")
async def get_dashboard_data():
    """
    Endpoint principal consumido pelo Dashboard.
    Retorna o estado atual das máquinas e KPIs.
    """
    return get_simulated_data()

@app.get("/demo/events")
async def get_demo_events():
    """
    Retorna lista de eventos (raw data) para tabela.
    """
    return generate_raw_events()

@app.get("/demo/export")
async def export_csv():
    """
    Exporta os eventos em formato CSV para download.
    """
    events = generate_raw_events()
    if not events:
        return Response(content="No data", media_type="text/plain")

    output = io.StringIO()
    # Define headers based on first item keys
    headers = events[0].keys()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(events)
    
    csv_content = output.getvalue()
    
    filename = f"telemetry_demo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
