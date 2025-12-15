import sys
import os
import json
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Mock env
os.environ["TELEMETRY_ENV"] = "field"

try:
    from backend.config import load_machines_from_driver_config, STARK_MACHINES
    from backend.models import CncMachineData
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def verify_models():
    print("--- Verifying Machine Models Configuration ---")
    
    # Reload machines to be sure
    machines = STARK_MACHINES
    
    if not machines:
        print("WARNING: No machines loaded.")
        return

    print(f"Loaded {len(machines)} machines.")
    
    for m in machines:
        print(f"\nID: {m.id}")
        print(f"Name: {m.name}")
        print(f"Model: {m.model}")
        
        if m.model == "FANUC Generic" or not m.model:
            print(f"❌ FAIL: Machine {m.id} has generic or empty model.")
        else:
            print(f"✅ OK: Machine {m.id} has specific model: {m.model}")

    # Verify CncMachineData instantiation (Simulate Offline Fallback)
    print("\n--- Verifying Offline Fallback Object ---")
    try:
        dummy_cfg = machines[0]
        offline_data = CncMachineData(
            machine_id=dummy_cfg.id,
            state="OFFLINE",
            controller_type="FANUC",
            model=dummy_cfg.model, # This is the key field we added
            timestamp=datetime.now().isoformat(),
            availability="UNAVAILABLE",
            execution_state="STOPPED"
        )
        
        json_out = offline_data.json()
        parsed = json.loads(json_out)
        
        if "model" in parsed and parsed["model"] == dummy_cfg.model:
             print(f"✅ OK: JSON serialization includes 'model': {parsed['model']}")
        else:
             print(f"❌ FAIL: JSON missing 'model' field. Got keys: {parsed.keys()}")
             
    except Exception as e:
        print(f"❌ FAIL: CncMachineData instantiation failed: {e}")

if __name__ == "__main__":
    verify_models()
