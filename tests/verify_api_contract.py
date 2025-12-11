import sys
import os
import json

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Mock env if needed
os.environ["TELEMETRY_ENV"] = "lab"

try:
    from backend.datasources import generate_raw_events
except ImportError:
    # Fallback
    sys.path.append(os.getcwd())
    from app.backend.datasources import generate_raw_events

def verify_contract():
    print("Verifying API Data Contract (generate_raw_events)...")
    
    # Generate events (will fetch from DB or return empty if DB empty, 
    # but we assume the simulator has run and populated some data)
    events = generate_raw_events(count=1)
    
    if not events:
        print("WARNING: No events returned. Cannot verify contract keys.")
        print("Please ensure the simulator has run and generated data.")
        sys.exit(0) # Not a failure of the script, but skipped verification
        
    sample = events[0]
    # print(f"Sample Row: {json.dumps(sample, default=str)}")
    
    expected_keys = {
        "id", "data", "maquina_id", "produto", "turno", 
        "tempo_ciclo_min", "pecas_boas", "pecas_refugo", 
        "parada_min", "motivo_parada"
    }
    
    actual_keys = set(sample.keys())
    missing = expected_keys - actual_keys
    
    if missing:
        print(f"FAILED: Missing keys in backend response: {missing}")
        sys.exit(1)
        
    print("SUCCESS: Backend response contains all required PT-BR keys for Frontend.")
    print(f"Keys verified: {sorted(list(actual_keys))}")

if __name__ == "__main__":
    verify_contract()
