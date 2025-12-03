
export type ControllerMode = 'MEM' | 'MDI' | 'AUTO' | 'EDIT' | 'MANUAL';
export type ExecutionState = 'ACTIVE' | 'READY' | 'STOPPED' | 'INTERRUPTED' | 'FEED_HOLD';
export type Availability = 'AVAILABLE' | 'UNAVAILABLE';

// Dados em tempo real de uma máquina CNC
export interface CncMachineData {
  machine_id: string; // ex: "CNC-01"
  controller_type: 'M70' | 'M80' | 'M800' | 'FANUC';
  timestamp: string;
  
  // MTConnect Availability
  availability: Availability;

  // Status
  execution_state: ExecutionState;
  controller_mode: ControllerMode;
  program_name: string; // ex: "O1234"
  current_block: string; // ex: "N100 G01 X10.5 Y20.0"
  current_tool: string; // ex: "T05"
  
  // Métricas Físicas
  spindle_load: number; // %
  spindle_speed: number; // RPM
  feed_rate: number; // mm/min
  feed_rate_override: number; // %
  
  // Histórico para Sparklines (últimos 20 pontos)
  load_history: number[];

  // Contadores
  part_count: number;
  run_time_min: number;
  
  // Alarmes
  active_alarm?: {
    code: string;
    message: string;
    severity: 'warning' | 'critical';
  } | null;
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
  source: 'python_pipeline' | 'browser_simulation';
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
