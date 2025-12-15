
export type ControllerMode = 'MEM' | 'MDI' | 'AUTO' | 'EDIT' | 'MANUAL';
export type ExecutionState = 'ACTIVE' | 'READY' | 'STOPPED' | 'INTERRUPTED' | 'FEED_HOLD';
export type Availability = 'AVAILABLE' | 'UNAVAILABLE';

// Contrato Canônico (Paridade com Backend TelemetrySample)
export interface TelemetrySample {
  machine_id: string;
  timestamp: string;
  state: string; // RUN, IDLE, ALARM, OFFLINE

  program_name?: string | null;
  current_block?: string | null;
  part_count: number;

  current_tool?: string | null;
  controller_mode?: string | null;

  spindle_load?: number | null;
  spindle_speed?: number | null;
  feed_rate?: number | null;
  feed_rate_override?: number | null;

  cycle_time_machine_s?: number | null;
  cycle_time_total_s?: number | null;

  active_alarm_code?: string | null;
  active_alarm_msg?: string | null;
  active_alarm_severity?: string | null;
}

// Dados Completos para Dashboard (Estende TelemetrySample)
export interface CncMachineData extends TelemetrySample {
  controller_type: 'M70' | 'M80' | 'M800' | 'FANUC';
  model?: string; // Modelo específico (ex: FANUC 0i-TF Plus)
  
  // MTConnect Availability (UI Derived)
  availability: Availability;

  // Status Mapeado (UI Derived)
  execution_state: ExecutionState;
  
  // Compatibilidade com UI antiga (se necessário, ou usar active_alarm_*)
  // O backend envia active_alarm como computed property se serializado, 
  // mas se não, o frontend pode reconstruir.
  active_alarm?: {
    code: string;
    message: string;
    severity: 'warning' | 'critical';
  } | null;

  // Histórico para Sparklines
  load_history: number[];

  // Dados Agregados
  run_time_min: number;
  
  // Status de Conexão
  connection_status?: 'ONLINE' | 'OFFLINE';
  connection_error?: string | null;
}

// Data types for Charts and Analytics
export interface MonthlyMetric {
  month: string;
  avg_oee: number;
}

export interface MachineMetric {
  maquina_id: string;
  oee: number;
}

export interface DowntimeMetric {
  motivo: string;
  minutos: number;
}

export interface ShiftMetric {
  turno: string;
  refugo_rate: number;
}

// Métricas Agregadas para o Dashboard
export interface DashboardData {
  machines: CncMachineData[];
  kpis: {
    global_oee: number;
    total_active_machines: number;
    avg_spindle_load: number;
    total_parts_shift: number;
    
    // Additional KPIs for Chat Context
    avg_oee: number;
    total_production: number;
    avg_scrap_rate: number;
    availability_rate: number;
  };
  
  // Analytical Data
  monthly_trend: MonthlyMetric[];
  machine_performance: MachineMetric[];
  downtime_reasons: DowntimeMetric[];
  shift_performance: ShiftMetric[];
  
  last_updated: string;
  source: 'python_pipeline' | 'browser_simulation' | 'multi_machine_aggregator' | 'field_mqtt';
}

// Contrato de Dados da Tabela de Eventos (PT-BR)
// Fonte: backend/datasources.py :: generate_raw_events()
export interface TelemetryEventRow {
  id: string;
  data: string;           // Timestamp ISO
  maquina_id: string;
  produto: string;
  turno: string;
  tempo_ciclo_min: number;
  pecas_boas: number;
  pecas_refugo: number;
  parada_min: number;
  motivo_parada: string;
}

// Chat Types
export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string; // ISO string
  isThinking?: boolean;
}
