
export const MACHINES = ['CNC-01 (M80)', 'CNC-02 (M70)', 'CNC-03 (M80)', 'VMC-A (Fanuc)', 'HMC-B (M800)'];
export const PROGRAMS = ['O0010 (Faceamento)', 'O1200 (Usinagem Eixo)', 'O5050 (Furação Base)', 'O9001 (Macro Probe)'];
export const TOOLS = ['T01 (Face Mill)', 'T02 (End Mill 10mm)', 'T03 (Drill 5mm)', 'T04 (Tap M6)', 'T05 (Probe)'];

// Alarmes reais baseados no manual Mitsubishi M70/M80
export const MITSUBISHI_ALARMS = [
  { code: 'M01', message: 'OPERATION ERROR', severity: 'warning', description: 'Erro de operação geral ou parada opcional ativa.' },
  { code: 'S01', message: 'SERVO ALARM: PR', severity: 'critical', description: 'Erro de detecção de posição no Servo Eixo X/Y/Z.' },
  { code: 'S52', message: 'SERVO WARNING: OVERLOAD', severity: 'warning', description: 'Sobrecarga térmica detectada no servo motor.' },
  { code: 'P32', message: 'ADDRESS ERROR', severity: 'critical', description: 'Endereço de memória inválido no programa NC.' },
  { code: 'Z55', message: 'R/IO I/F COM. ERROR', severity: 'critical', description: 'Falha de comunicação com módulos de I/O remotos.' },
  { code: 'Y03', message: 'AMP. UN-EQUIPPED', severity: 'critical', description: 'Amplificador do servo não detectado.' },
  { code: 'EMG', message: 'EMERGENCY STOP', severity: 'critical', description: 'Botão de emergência pressionado ou circuito aberto.' }
];

export const SIMULATION_CONFIG = {
  REFRESH_RATE_MS: 2000,
  MAX_RPM: 12000,
  MAX_FEED: 10000,
  AVAILABILITY_CHANCE: 0.98 // Chance de estar conectado à rede
};
