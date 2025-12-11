import sys
import os
import json
from datetime import datetime

# Add app root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.adapters import FanucAdapter

def test_fanuc_adapter():
    print("=== Smoke Test: FanucAdapter Ingestion ===")
    
    adapter = FanucAdapter("STARK_TORNO_PILOTO")
    
    # 1. Simulate StateData (JSON from Driver)
    state_payload = json.dumps({
        "machine": "STARK_TORNO_PILOTO",
        "execution": "ACTIVE",
        "mode": "MEM",
        "alarm": False,
        "tool_num": 5,
        "fovr": 100,
        "feed": 150.5
    })
    
    print(f"[INPUT] StateData: {state_payload}")
    sample = adapter.ingest("StateData", state_payload)
    
    # Assertions
    assert sample.state == "RUN", f"Expected RUN, got {sample.state}"
    assert sample.feed_rate == 150.5, f"Expected feed 150.5, got {sample.feed_rate}"
    print("[PASS] StateData mapping correct")

    # 2. Simulate ProductionData
    prod_payload = json.dumps({
        "program_name": "O1234",
        "pieces_produced": 150,
        "cycle_time": 45000 # ms
    })
    
    print(f"[INPUT] ProductionData: {prod_payload}")
    sample = adapter.ingest("ProductionData", prod_payload)
    
    # Assertions - State should persist
    assert sample.state == "RUN", "State lost after partial update"
    assert sample.part_count == 150, f"Expected 150 parts, got {sample.part_count}"
    assert sample.program_name == "O1234", f"Expected prog O1234, got {sample.program_name}"
    assert sample.cycle_time_machine_s == 45.0, f"Expected 45.0s cycle, got {sample.cycle_time_machine_s}"
    print("[PASS] ProductionData mapping correct")
    
    # 3. Simulate SpindleData
    spindle_payload = json.dumps({
        "speed": 1200,
        "load": 45.5
    })
    
    print(f"[INPUT] SpindleData: {spindle_payload}")
    sample = adapter.ingest("SpindleData", spindle_payload)
    
    assert sample.spindle_speed == 1200, f"Expected 1200 RPM, got {sample.spindle_speed}"
    assert sample.spindle_load == 45.5, f"Expected 45.5% Load, got {sample.spindle_load}"
    print("[PASS] SpindleData mapping correct")
    
    print("\n=== Smoke Test PASSED ===")

if __name__ == "__main__":
    test_fanuc_adapter()
