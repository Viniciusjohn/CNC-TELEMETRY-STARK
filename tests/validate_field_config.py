import os
import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Force FIELD environment
os.environ["TELEMETRY_ENV"] = "field"

from backend.config import load_machines_from_driver_config, IS_LAB, IS_FIELD, STARK_MACHINES

def validate_field_config():
    print("--- VALIDATION: FIELD MODE CONFIGURATION ---")
    print(f"ENV: {os.getenv('TELEMETRY_ENV')}")
    print(f"IS_FIELD: {IS_FIELD}")
    print(f"IS_LAB: {IS_LAB}")
    
    machines = load_machines_from_driver_config()
    print(f"\nLoaded {len(machines)} machines from Driver Config.")
    
    if not machines:
        print("FAIL: No machines loaded. Check config.machines.yml")
        sys.exit(1)
        
    # Check for Real IPs
    real_ip_detected = False
    for m in machines:
        print(f"Machine [{m.id}]: IP={m.ip}")
        if m.ip != "127.0.0.1" and m.ip != "localhost":
            real_ip_detected = True
            
    if real_ip_detected:
        print("\nSUCCESS: Detected Field IPs (non-localhost). Configuration is pointing to real hardware.")
    else:
        print("\nWARNING: Only localhost IPs detected. Is config.machines.yml correct for FIELD?")
        # It might be that the field config currently HAS localhost for testing, but we expect real IPs for STARK.
        # Based on previous context, STARK config has 192.168.1.x
        
    if IS_FIELD and not IS_LAB:
        print("SUCCESS: Environment variables correctly set for FIELD mode.")
    else:
        print("FAIL: Environment variables not correct.")
        sys.exit(1)

if __name__ == "__main__":
    validate_field_config()
