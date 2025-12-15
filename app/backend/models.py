from typing import List, Dict, Optional
from pydantic import BaseModel

# --- Canonical Data Contract ---
class TelemetrySample(BaseModel):
    """
    Representação canônica de uma amostra de telemetria CNC.
    Este é o contrato base para todos os perfis de controladores.
    Campos não suportados por um driver específico devem ser None.
    """
    machine_id: str
    timestamp: str
    
    # Estado Normalizado (RUN, IDLE, ALARM, OFFLINE)
    state: str 
    
    # Dados de Produção
    program_name: Optional[str] = None
    current_block: Optional[str] = None
    part_count: int = 0
    
    # Ferramentas e Modos
    current_tool: Optional[str] = None
    controller_mode: Optional[str] = None # MEM, MDI, AUTO
    
    # Sensores / Cargas
    spindle_load: Optional[float] = None
    spindle_speed: Optional[float] = None # RPM
    feed_rate: Optional[float] = None     # mm/min
    feed_rate_override: Optional[float] = None
    
    # Tempos de Ciclo (Último ciclo completo ou corrente)
    cycle_time_machine_s: Optional[float] = None
    cycle_time_total_s: Optional[float] = None
    
    # Alarmes Ativos
    active_alarm_code: Optional[str] = None
    active_alarm_msg: Optional[str] = None
    active_alarm_severity: Optional[str] = None # warning, critical

class CncMachineData(TelemetrySample):
    """
    Modelo estendido para o Dashboard API.
    Inclui campos calculados ou históricos que não vêm diretamente do driver.
    """
    controller_type: str
    model: Optional[str] = None # Modelo Específico (ex: FANUC 0i-TF Plus)
    availability: str # AVAILABLE | UNAVAILABLE (MTConnect concept)
    execution_state: str # Mapeado de state para compatibilidade UI (ACTIVE, READY, STOPPED)
    
    # Histórico para Sparklines (últimos 20 pontos)
    load_history: List[float] = []
    
    # Dados calculados / agregados
    run_time_min: int = 0
    
    # Status de Conexão (Camada de Aplicação)
    connection_status: str = "ONLINE" # ONLINE | OFFLINE
    connection_error: Optional[str] = None
    
    # Adapter auxiliar para manter compatibilidade com active_alarm dict da UI antiga
    @property
    def active_alarm(self) -> Optional[Dict]:
        if self.active_alarm_code:
            return {
                "code": self.active_alarm_code,
                "message": self.active_alarm_msg,
                "severity": self.active_alarm_severity or "warning"
            }
        return None

class DashboardData(BaseModel):
    machines: List[CncMachineData]
    kpis: Dict
    monthly_trend: List[Dict]
    machine_performance: List[Dict]
    downtime_reasons: List[Dict]
    shift_performance: List[Dict]
    last_updated: str
    source: str
