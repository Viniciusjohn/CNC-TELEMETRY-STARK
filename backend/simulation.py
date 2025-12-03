import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel

# Constants
MACHINES = ["M70-A (Milling)", "Fanuc-B (Lathe)", "M80-C (5-Axis)", "M70-D (Grinding)"]
PROGRAMS = ["O1001", "O1002", "O1234", "O5000", "O9001"]
TOOLS = ["T01", "T02", "T05", "T10", "T12"]
MITSUBISHI_ALARMS = [
    {"code": "S01", "message": "Servo Alarm: PR Error", "severity": "critical"},
    {"code": "M01", "message": "Operation Error", "severity": "warning"},
    {"code": "Y05", "message": "Thermal Overload", "severity": "critical"},
    {"code": "Z55", "message": "Encoder Battery Low", "severity": "warning"},
]

class CncMachineData(BaseModel):
    machine_id: str
    controller_type: str
    timestamp: str
    availability: str
    execution_state: str
    controller_mode: str
    program_name: str
    current_block: str
    current_tool: str
    spindle_load: float
    spindle_speed: float
    feed_rate: float
    feed_rate_override: float
    load_history: List[float]
    part_count: int
    run_time_min: int
    active_alarm: Optional[Dict] = None

class DashboardData(BaseModel):
    machines: List[CncMachineData]
    kpis: Dict
    monthly_trend: List[Dict]
    machine_performance: List[Dict]
    downtime_reasons: List[Dict]
    shift_performance: List[Dict]
    last_updated: str
    source: str

# Internal State
machines_state = {}

def initialize_machine(machine_id: str) -> dict:
    return {
        "machine_id": machine_id,
        "controller_type": "M70" if "M70" in machine_id else ("FANUC" if "Fanuc" in machine_id else "M80"),
        "timestamp": datetime.now().isoformat(),
        "availability": "AVAILABLE",
        "execution_state": "ACTIVE",
        "controller_mode": "MEM",
        "program_name": random.choice(PROGRAMS),
        "current_block": "N10 G01 X100 F2000",
        "current_tool": random.choice(TOOLS),
        "spindle_load": 0.0,
        "spindle_speed": 0.0,
        "feed_rate": 0.0,
        "feed_rate_override": 100.0,
        "load_history": [0.0] * 20,
        "part_count": random.randint(50, 200),
        "run_time_min": random.randint(100, 400),
        "active_alarm": None
    }

def get_simulated_data() -> dict:
    global machines_state
    
    # Initialize if empty
    for m_id in MACHINES:
        if m_id not in machines_state:
            machines_state[m_id] = initialize_machine(m_id)

    # Update State
    updated_machines = []
    for m_id in MACHINES:
        m = machines_state[m_id]
        
        # Simulate network availability
        if random.random() > 0.99: # 1% chance of going offline
            m["availability"] = "UNAVAILABLE"
            m["execution_state"] = "STOPPED"
            m["spindle_load"] = 0.0
            m["spindle_speed"] = 0.0
        else:
            m["availability"] = "AVAILABLE"

        if m["availability"] == "AVAILABLE":
            # State changes
            if random.random() > 0.95:
                states = ["ACTIVE", "READY", "STOPPED", "FEED_HOLD"]
                m["execution_state"] = random.choice(states)
                
                if m["execution_state"] == "STOPPED" and random.random() > 0.7:
                    alm = random.choice(MITSUBISHI_ALARMS)
                    m["active_alarm"] = alm
                else:
                    m["active_alarm"] = None

            # Physics
            if m["execution_state"] == "ACTIVE":
                m["spindle_speed"] = 8000 + random.randint(-500, 500)
                base_load = 40 + random.uniform(-5, 15)
                m["spindle_load"] = base_load + (35 if random.random() > 0.85 else 0)
                m["feed_rate"] = 2000 + random.randint(-200, 200)
                m["current_block"] = f"N{random.randint(100, 900)} G01 X{random.uniform(0, 500):.1f} Y{random.uniform(0, 500):.1f}"
            elif m["execution_state"] in ["READY", "FEED_HOLD"]:
                m["spindle_speed"] = 8000 if m["execution_state"] == "FEED_HOLD" else 0
                m["spindle_load"] = 5 if m["execution_state"] == "FEED_HOLD" else 0
                m["feed_rate"] = 0
            else:
                m["spindle_speed"] = 0
                m["spindle_load"] = 0
                m["feed_rate"] = 0

        # Update History
        m["load_history"] = m["load_history"][1:] + [m["spindle_load"]]
        m["timestamp"] = datetime.now().isoformat()
        updated_machines.append(m)

    # KPIs
    available = [m for m in updated_machines if m["availability"] == "AVAILABLE"]
    active_count = len([m for m in available if m["execution_state"] == "ACTIVE"])
    total_avail = len(available)
    global_oee = active_count / total_avail if total_avail > 0 else 0.0
    
    avg_load = sum(m["spindle_load"] for m in available) / total_avail if total_avail > 0 else 0.0
    total_parts = sum(m["part_count"] for m in updated_machines)

    # Static/Slow changing data
    monthly_trend = [
        {"month": "Jan", "avg_oee": 0.72}, {"month": "Fev", "avg_oee": 0.75}, 
        {"month": "Mar", "avg_oee": 0.78}, {"month": "Abr", "avg_oee": 0.80},
        {"month": "Mai", "avg_oee": 0.82}, {"month": "Jun", "avg_oee": 0.79},
        {"month": "Jul", "avg_oee": 0.81}, {"month": "Ago", "avg_oee": 0.85},
        {"month": "Set", "avg_oee": 0.88}, {"month": "Out", "avg_oee": 0.84},
        {"month": "Nov", "avg_oee": 0.86}, {"month": "Dez", "avg_oee": 0.89}
    ]
    
    downtime_reasons = [
        {"motivo": "Troca de Ferramenta", "minutos": 45},
        {"motivo": "Alarmes S01/S52", "minutos": 20},
        {"motivo": "Setup de Peça", "minutos": 35},
    ]
    
    machine_perf = [
        {"maquina_id": m["machine_id"], "oee": random.uniform(0.7, 0.95) if m["availability"] == "AVAILABLE" else 0}
        for m in updated_machines
    ]
    
    shift_perf = [
        {"turno": "Turno A", "refugo_rate": 0.02},
        {"turno": "Turno B", "refugo_rate": 0.04},
        {"turno": "Turno C", "refugo_rate": 0.01}
    ]

    return {
        "machines": updated_machines,
        "kpis": {
            "global_oee": global_oee,
            "total_active_machines": active_count,
            "avg_spindle_load": avg_load,
            "total_parts_shift": total_parts,
            "avg_oee": global_oee,
            "total_production": total_parts,
            "avg_scrap_rate": 0.02,
            "availability_rate": len(available) / len(MACHINES)
        },
        "monthly_trend": monthly_trend,
        "machine_performance": machine_perf,
        "downtime_reasons": downtime_reasons,
        "shift_performance": shift_perf,
        "last_updated": datetime.now().isoformat(),
        "source": "python_pipeline"
    }

def generate_raw_events(count=100):
    events = []
    reasons = ['Troca Ferramenta', 'Setup', 'Alarme S01', 'Alarme M01', 'Sem Material']
    products = ['Eixo A-10', 'Base B-20', 'Flange C-30']
    
    for i in range(count):
        events.append({
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "machine_id": MACHINES[i % len(MACHINES)].split()[0],
            "state": random.choice(["RUN", "IDLE", "ALARM"]),
            "rpm": random.randint(0, 10000),
            "program": random.choice(PROGRAMS),
            # Extra fields matching UI expectations for "Raw Data"
            "product": products[i % len(products)],
            "shift": ["A", "B", "C"][i % 3],
            "cycle_time": round(4 + random.random(), 1),
            "good_parts": random.randint(0, 50),
            "scrap_parts": random.randint(0, 2),
            "stop_min": random.randint(0, 20),
            "stop_reason": random.choice(reasons) if random.random() > 0.7 else "N/A"
        })
    return events
