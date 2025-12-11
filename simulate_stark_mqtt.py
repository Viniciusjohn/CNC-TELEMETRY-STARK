import time
import json
import random
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = "localhost"
PORT = 1883

MACHINES = [
    "STARK_TORNO_PILOTO",
    "STARK_TORNO_02",
    "STARK_CENTRO_01"
]

def get_base_payload(machine_id, veneer):
    return {
        "observation": {
            "time": int(time.time() * 1000),
            "machine": machine_id,
            "name": veneer,
            "marker": [{"type": "path", "number": 1}]
        }
    }

def simulate():
    client = mqtt.Client("StarkSimulatorPython")
    try:
        client.connect(BROKER, PORT, 60)
        print(f"Conectado ao broker {BROKER}:{PORT}")
    except Exception as e:
        print(f"Erro ao conectar no broker: {e}")
        return

    part_count = 1000
    
    print("Iniciando simulação STARK Realista... (Ctrl+C para parar)")
    
    # Estado inicial de cada máquina
    machine_states = {
        m_id: {
            "status": "ACTIVE", 
            "last_change": time.time(), 
            "parts": 1000,
            "rpm": 0
        } 
        for m_id in MACHINES
    }

    while True:
        current_time = time.time()

        for m_id in MACHINES:
            state = machine_states[m_id]
            
            # Lógica de Troca de Estado (Simula ciclo de máquina)
            # A cada 15-30s, troca entre ACTIVE (Usinando) e READY (Parada/Troca)
            time_in_state = current_time - state["last_change"]
            
            if state["status"] == "ACTIVE" and time_in_state > random.randint(15, 30):
                # Terminou ciclo -> Vai para IDLE
                state["status"] = "READY"
                state["last_change"] = current_time
                state["parts"] += 1 # Conta peça no final do ciclo
                state["rpm"] = 0
                print(f"[{m_id}] Peça pronta! Total: {state['parts']} -> IDLE")
                
            elif state["status"] == "READY" and time_in_state > random.randint(5, 10):
                # Terminou troca -> Volta a Usinar
                state["status"] = "ACTIVE"
                state["last_change"] = current_time
                state["rpm"] = random.randint(800, 1200)
                print(f"[{m_id}] Iniciando ciclo -> RUN")

            # 1. Publica STATE
            # Mapeamento: ACTIVE -> execution: ACTIVE / READY -> execution: READY
            payload_state = get_base_payload(m_id, "state")
            payload_state["state"] = {
                "time": current_time,
                "data": {
                    "mode": "AUTOMATIC",
                    "execution": state["status"], 
                    "override": {"feed": 100 if state["status"] == "ACTIVE" else 0}
                }
            }
            client.publish(f"fanuc/{m_id}/state", json.dumps(payload_state))

            # 2. Publica SPINDLE
            # Varia RPM se estiver ACTIVE
            current_rpm = state["rpm"]
            if state["status"] == "ACTIVE":
                current_rpm = random.randint(state["rpm"] - 50, state["rpm"] + 50)
            
            payload_spindle = get_base_payload(m_id, "spindle")
            payload_spindle["state"] = {
                "time": current_time,
                "data": {
                    "number": 1,
                    "name": "S1",
                    "speed": current_rpm,
                    "load": random.uniform(10, 50) if state["status"] == "ACTIVE" else 0
                }
            }
            client.publish(f"fanuc/{m_id}/spindle", json.dumps(payload_spindle))

            # 3. Publica PRODUCTION
            payload_prod = get_base_payload(m_id, "production")
            payload_prod["state"] = {
                "time": current_time,
                "data": {
                    "program": {
                        "current": {"name": "O1234", "number": 1234}
                    },
                    "pieces": {
                        "produced": state["parts"]
                    }
                }
            }
            client.publish(f"fanuc/{m_id}/production", json.dumps(payload_prod))

        time.sleep(1) # 1Hz update rate

if __name__ == "__main__":
    simulate()
