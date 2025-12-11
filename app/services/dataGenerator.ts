
import { DashboardData, CncMachineData, ExecutionState } from '../types';
import { MACHINES, PROGRAMS, TOOLS, MITSUBISHI_ALARMS, SIMULATION_CONFIG } from '../constants';

const randomFloat = (min: number, max: number) => Math.random() * (max - min) + min;
const randomInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;
const randomChoice = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

// Estado interno persistente da simulação
const machinesState: Record<string, CncMachineData> = {};

const initializeMachine = (id: string): CncMachineData => ({
    machine_id: id,
    controller_type: id.includes('M70') ? 'M70' : id.includes('Fanuc') ? 'FANUC' : 'M80',
    timestamp: new Date().toISOString(),
    availability: 'AVAILABLE',
    execution_state: 'ACTIVE',
    controller_mode: 'MEM',
    program_name: randomChoice(PROGRAMS),
    current_block: 'N10 G01 X100 F2000',
    current_tool: randomChoice(TOOLS),
    spindle_load: 0,
    spindle_speed: 0,
    feed_rate: 0,
    feed_rate_override: 100,
    load_history: Array(20).fill(0),
    part_count: randomInt(50, 200),
    run_time_min: randomInt(100, 400),
    active_alarm: null
});

export const generateSimulatedDashboardData = (): DashboardData => {
    // Inicializa
    MACHINES.forEach(id => {
        if (!machinesState[id]) {
            machinesState[id] = initializeMachine(id);
        }
    });

    const machines = MACHINES.map(id => {
        const m = machinesState[id];
        
        // Simula falha de rede/Adapter (MTConnect UNAVAILABLE)
        if (Math.random() > SIMULATION_CONFIG.AVAILABILITY_CHANCE) {
            m.availability = 'UNAVAILABLE';
            m.execution_state = 'STOPPED'; // Ou unknown
            m.spindle_load = 0;
            m.spindle_speed = 0;
            m.timestamp = new Date().toISOString();
            return { ...m };
        } else {
            m.availability = 'AVAILABLE';
        }

        // Mudança de estado normal
        if (Math.random() > 0.95) {
            const states: ExecutionState[] = ['ACTIVE', 'READY', 'STOPPED', 'FEED_HOLD'];
            m.execution_state = randomChoice(states);
            
            if (m.execution_state === 'STOPPED' && Math.random() > 0.7) {
                const alm = randomChoice(MITSUBISHI_ALARMS);
                m.active_alarm = { ...alm, severity: alm.severity as 'warning' | 'critical' };
            } else {
                m.active_alarm = null;
            }
        }

        // Física da máquina
        let currentLoad = 0;
        if (m.execution_state === 'ACTIVE') {
            m.spindle_speed = 8000 + randomInt(-500, 500);
            currentLoad = 40 + randomFloat(-5, 15);
            m.feed_rate = 2000 + randomInt(-200, 200);
            m.current_block = `N${randomInt(100, 900)} G01 X${randomFloat(0, 500).toFixed(1)} Y${randomFloat(0, 500).toFixed(1)}`;
            
            // Simula corte pesado
            if (Math.random() > 0.85) currentLoad += 35;
        } else if (m.execution_state === 'READY' || m.execution_state === 'FEED_HOLD') {
            m.spindle_speed = m.execution_state === 'FEED_HOLD' ? 8000 : 0;
            currentLoad = m.execution_state === 'FEED_HOLD' ? 5 : 0;
            m.feed_rate = 0;
        } else {
            m.spindle_speed = 0;
            currentLoad = 0;
            m.feed_rate = 0;
        }

        m.spindle_load = currentLoad;
        m.load_history = [...m.load_history.slice(1), currentLoad];
        m.timestamp = new Date().toISOString();
        return { ...m };
    });

    // Cálculos de KPI
    const availableMachines = machines.filter(m => m.availability === 'AVAILABLE');
    const activeCount = availableMachines.filter(m => m.execution_state === 'ACTIVE').length;
    const avgLoad = availableMachines.length > 0 
        ? availableMachines.reduce((acc, m) => acc + m.spindle_load, 0) / availableMachines.length 
        : 0;
    
    const globalOee = availableMachines.length > 0 ? activeCount / availableMachines.length : 0;

    // Dados auxiliares estáticos (simulados) para analytics
    const machinePerformance = machines.map(m => ({
        maquina_id: m.machine_id,
        oee: m.availability === 'UNAVAILABLE' ? 0 : (m.execution_state === 'ACTIVE' ? randomFloat(0.7, 0.95) : randomFloat(0.3, 0.6))
    }));

    // ... (restante dos dados estáticos como no original) ...
    const downtimeReasons = [
        { motivo: 'Troca de Ferramenta', minutos: randomInt(10, 50) },
        { motivo: 'Alarmes S01/S52', minutos: randomInt(5, 25) },
        { motivo: 'Setup de Peça', minutos: randomInt(15, 60) },
    ].sort((a, b) => b.minutos - a.minutos);

    const shiftPerformance = [
        { turno: 'Turno A', refugo_rate: randomFloat(0.01, 0.05) },
        { turno: 'Turno B', refugo_rate: randomFloat(0.02, 0.06) },
        { turno: 'Turno C', refugo_rate: randomFloat(0.00, 0.03) }
    ];

    const monthlyTrend = [
        { month: 'Jan', avg_oee: 0.72 }, { month: 'Fev', avg_oee: 0.75 }, { month: 'Mar', avg_oee: 0.78 },
        { month: 'Abr', avg_oee: 0.80 }, { month: 'Mai', avg_oee: 0.82 }, { month: 'Jun', avg_oee: 0.79 },
        { month: 'Jul', avg_oee: 0.81 }, { month: 'Ago', avg_oee: 0.85 }, { month: 'Set', avg_oee: 0.88 },
        { month: 'Out', avg_oee: 0.84 }, { month: 'Nov', avg_oee: 0.86 }, { month: 'Dez', avg_oee: 0.89 },
    ];

    return {
        machines,
        kpis: {
            global_oee: globalOee,
            total_active_machines: activeCount,
            avg_spindle_load: avgLoad,
            total_parts_shift: machines.reduce((acc, m) => acc + m.part_count, 0),
            avg_oee: globalOee,
            total_production: machines.reduce((acc, m) => acc + m.part_count, 0),
            avg_scrap_rate: 0.02,
            availability_rate: availableMachines.length / machines.length
        },
        monthly_trend: monthlyTrend,
        machine_performance: machinePerformance,
        downtime_reasons: downtimeReasons,
        shift_performance: shiftPerformance,
        last_updated: new Date().toISOString(),
        source: 'browser_simulation'
    };
};

export const generateRawData = () => {
  const data = [];
  const machines = MACHINES;
  const reasons = ['Troca Ferramenta', 'Setup', 'Alarme S01', 'Alarme M01', 'Sem Material'];
  const products = ['Eixo A-10', 'Base B-20', 'Flange C-30'];

  for (let i = 0; i < 100; i++) {
    data.push({
      id: i,
      data: new Date(Date.now() - i * 3600000).toISOString(),
      maquina_id: machines[i % machines.length].split(' ')[0],
      produto: products[i % products.length],
      turno: ['A', 'B', 'C'][i % 3],
      tempo_ciclo_min: (4 + Math.random()).toFixed(1),
      pecas_boas: Math.floor(Math.random() * 50),
      pecas_refugo: Math.floor(Math.random() * 2),
      parada_min: Math.floor(Math.random() * 20),
      motivo_parada: Math.random() > 0.7 ? reasons[Math.floor(Math.random() * reasons.length)] : 'N/A'
    });
  }
  return data;
};

export const convertToCSV = (objArray: any[]) => {
    const array = typeof objArray !== 'object' ? JSON.parse(objArray) : objArray;
    let str = '';
    
    if (array.length === 0) return '';

    const headers = Object.keys(array[0]).join(',');
    str += headers + '\r\n';

    for (let i = 0; i < array.length; i++) {
        let line = '';
        for (const index in array[i]) {
            if (line !== '') line += ',';
            const val = array[i][index];
            line += typeof val === 'string' && val.includes(',') ? `"${val}"` : val;
        }
        str += line + '\r\n';
    }
    return str;
};
