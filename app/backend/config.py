import os
import yaml
import logging
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path

# Environment: "lab" or "field"
TELEMETRY_ENV = os.getenv("TELEMETRY_ENV", "lab").lower()
IS_LAB = TELEMETRY_ENV == "lab"
IS_FIELD = TELEMETRY_ENV == "field"

# Logger
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "fanuc")

@dataclass
class MachineConfig:
    id: str
    name: str
    ip: str
    model: str

def load_machines_from_driver_config() -> List[MachineConfig]:
    """
    Lê a configuração do driver fanuc para garantir Single Source of Truth.
    """
    # Path relativo: app/backend/config.py -> fanuc-driver/config.machines.yml
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    # Patch Demo: Usa arquivo de config específico para simulação se estiver em modo LAB
    config_filename = "config.machines.demo.yml" if IS_LAB else "config.machines.yml"
    config_path = base_dir / "fanuc-driver" / config_filename
    
    logger.info(f"Carregando configuração de máquinas (Driver): {config_filename} [Env: {TELEMETRY_ENV}]")
    
    machines = []
    
    if not config_path.exists():
        logger.warning(f"Configuração do Driver não encontrada em {config_path}. Usando defaults.")
        return []

    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            
        if not data or 'machines' not in data:
            return []
            
        for m in data['machines']:
            if not m.get('enabled', False):
                continue
                
            mid = m.get('id')
            # Tenta extrair IP da configuração complexa do Ladder99
            # Chave esperada: "l99.driver.fanuc.FanucMachine, fanuc"
            net_config = m.get('l99.driver.fanuc.FanucMachine, fanuc', {}).get('net', {})
            ip = net_config.get('ip', '127.0.0.1')
            
            # Mapeamento de Modelos STARK Brasil
            # Baseado em:
            # STARK_TORNO_PILOTO -> FANUC 0i-TF Plus
            # STARK_TORNO_02     -> FANUC 0i-TF
            # STARK_CENTRO_01    -> FANUC 0i-MD
            
            name = mid.replace('_', ' ').title()
            model = "FANUC Generic"
            
            if "TORNO_PILOTO" in mid:
                model = "FANUC 0i-TF Plus"
            elif "TORNO_02" in mid:
                model = "FANUC 0i-TF"
            elif "CENTRO_01" in mid:
                model = "FANUC 0i-MD"
            
            machines.append(MachineConfig(
                id=mid,
                name=name,
                ip=ip,
                model=model
            ))
            
        logger.info(f"Carregadas {len(machines)} máquinas do driver config.")
        return machines
        
    except Exception as e:
        logger.error(f"Erro ao ler config do driver: {e}")
        return []

# Carrega configuração dinâmica
_dynamic_machines = load_machines_from_driver_config()

if _dynamic_machines:
    STARK_MACHINES = _dynamic_machines
else:
    # Fallback / Defaults se não conseguir ler o driver
    STARK_MACHINES: List[MachineConfig] = [
        MachineConfig(
            id="STARK_TORNO_PILOTO",
            name="Torno FANUC 0i-TF Plus",
            ip=os.getenv("FANUC_STARK_TORNO_PILOTO_IP", "192.168.1.101"), 
            model="0i-TF Plus",
        ),
        # Mantemos outros exemplos apenas se necessário, mas em prod só o que estiver no driver vale.
    ]

STARK_MACHINES_BY_ID: Dict[str, MachineConfig] = {m.id: m for m in STARK_MACHINES}
