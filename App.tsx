
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Server, Activity, Cpu, Gauge, AlertOctagon, PlayCircle, MessageSquare, BarChart3, 
  Wifi, WifiOff, Zap, Box, Clock, Download, Palette
} from 'lucide-react';
import { dashboardApi } from './services/dashboardApi';
import { DashboardData, CncMachineData } from './types';
import { CodexChat } from './components/CodexChat';
import { LoadSparkline, OeeTrendChart, DowntimeParetoChart, MachinePerformanceChart } from './components/Charts';
import { convertToCSV, generateRawData } from './services/dataGenerator';

// Presets de cores para personalização do usuário
const CHART_COLORS = [
    { name: 'Blue', value: '#3b82f6' },   // Default
    { name: 'Cyan', value: '#06b6d4' },   // Mitsubishi Style
    { name: 'Violet', value: '#8b5cf6' }, // Modern
    { name: 'Amber', value: '#f59e0b' },  // High Contrast
];

// Componente Industrial HMI para card de máquina
const MachinePanel: React.FC<{ machine: CncMachineData, oeeTrend: number[], chartColor: string }> = ({ machine, oeeTrend, chartColor }) => {
    const isOffline = machine.availability === 'UNAVAILABLE';
    const isRunning = machine.execution_state === 'ACTIVE' && !isOffline;
    const isError = (machine.execution_state === 'STOPPED' || machine.active_alarm) && !isOffline;
    const isHold = machine.execution_state === 'FEED_HOLD' && !isOffline;

    // Cores de status estilo PLC
    let borderColor = 'border-slate-700';
    let statusBg = 'bg-slate-800';
    let statusText = 'text-slate-400';
    
    if (isOffline) {
        borderColor = 'border-slate-800';
        statusBg = 'bg-slate-900';
        statusText = 'text-slate-600';
    } else if (isRunning) {
        borderColor = 'border-emerald-600';
        statusBg = 'bg-emerald-950/40';
        statusText = 'text-emerald-400';
    } else if (isError) {
        borderColor = 'border-rose-600';
        statusBg = 'bg-rose-950/40';
        statusText = 'text-rose-400';
    } else if (isHold) {
        borderColor = 'border-amber-600';
        statusBg = 'bg-amber-950/40';
        statusText = 'text-amber-400';
    }

    return (
        <div className={`relative bg-slate-900 border-l-4 ${borderColor} border-y border-r border-slate-800 rounded-r-md p-0 overflow-hidden shadow-md flex flex-col h-full font-mono`}>
            {/* Header: ID e Status */}
            <div className={`px-3 py-2 flex justify-between items-center border-b border-slate-800 ${statusBg}`}>
                <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-sm ${isOffline ? 'bg-slate-600' : isRunning ? 'bg-emerald-500 animate-pulse' : isError ? 'bg-rose-500 animate-pulse' : 'bg-amber-500'}`} />
                    <span className="text-lg font-bold text-white tracking-widest">{machine.machine_id}</span>
                </div>
                <span className={`text-xs font-bold uppercase ${statusText}`}>
                    {isOffline ? 'NO NET' : machine.execution_state}
                </span>
            </div>

            {/* Corpo: Dados Principais */}
            <div className="p-3 flex-1 flex flex-col gap-3 relative">
                {isOffline && (
                    <div className="absolute inset-0 bg-slate-950/80 z-10 flex items-center justify-center backdrop-blur-[1px]">
                        <div className="flex flex-col items-center text-slate-500">
                            <WifiOff className="w-8 h-8 mb-2" />
                            <span className="text-xs font-bold">OFFLINE</span>
                        </div>
                    </div>
                )}

                {/* Alarm Zone */}
                {machine.active_alarm && (
                    <div className="bg-rose-950 border border-rose-600 text-rose-100 px-2 py-1.5 text-xs font-bold animate-pulse flex items-center gap-2">
                        <AlertOctagon className="w-4 h-4 shrink-0" />
                        <span className="truncate">{machine.active_alarm.code}: {machine.active_alarm.message}</span>
                    </div>
                )}

                {/* Program & Tool */}
                <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 uppercase">
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                        <span className="block text-slate-500 mb-0.5">Program</span>
                        <span className="text-indigo-300 font-bold text-xs truncate block">{machine.program_name}</span>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                        <span className="block text-slate-500 mb-0.5">Tool</span>
                        <span className="text-white font-bold text-xs">{machine.current_tool}</span>
                    </div>
                </div>

                {/* Digital Readouts (DRO) */}
                <div className="space-y-2">
                    {/* Load */}
                    <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-bold w-12">LOAD</span>
                        <div className="flex-1 h-6 bg-slate-950 rounded border border-slate-800 relative mx-2 overflow-hidden">
                            <div 
                                className={`h-full transition-all duration-300 ${machine.spindle_load > 90 ? 'bg-rose-600' : 'bg-blue-600'}`}
                                style={{ width: `${machine.spindle_load}%` }}
                            />
                            <div className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-white z-10 mix-blend-difference">
                                {machine.spindle_load.toFixed(0)}%
                            </div>
                        </div>
                    </div>
                    {/* RPM */}
                    <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-bold w-12">RPM</span>
                        <span className="text-emerald-400 font-bold text-sm tracking-wider">{machine.spindle_speed.toFixed(0)}</span>
                    </div>
                    {/* Feed */}
                    <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-bold w-12">FEED</span>
                        <span className="text-white font-bold text-sm tracking-wider">{machine.feed_rate} <span className="text-[9px] text-slate-600">mm/min</span></span>
                    </div>
                </div>

                {/* Sparkline Area - Spindle Load History & OEE Trend */}
                <div className="mt-auto grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/50">
                    <div className="h-12 w-full">
                         <div className="text-[8px] text-slate-500 font-bold mb-0.5">SPINDLE LOAD</div>
                         <LoadSparkline 
                            data={machine.load_history} 
                            color={isError ? '#f43f5e' : chartColor} 
                         />
                    </div>
                    <div className="h-12 w-full">
                         <div className="text-[8px] text-slate-500 font-bold mb-0.5">OEE TREND</div>
                         <LoadSparkline 
                            data={oeeTrend} 
                            color="#10b981" 
                         />
                    </div>
                </div>
            </div>
            
            {/* Footer: Counters */}
            <div className="px-3 py-1.5 bg-slate-950 border-t border-slate-800 flex justify-between text-[10px] text-slate-500">
                <span>CNT: {machine.part_count}</span>
                <span>{machine.controller_type}</span>
            </div>
        </div>
    );
};

const App: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [rawData, setRawData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'monitor' | 'analytics' | 'codex' | 'data'>('monitor');
  const [chartColor, setChartColor] = useState(CHART_COLORS[0].value);

  const loadData = useCallback(async () => {
    try {
      const dashboardData = await dashboardApi.fetchDashboardData();
      setData(dashboardData);
      
      // Se estiver simulando via Python, busca os eventos do backend
      if (dashboardData.source === 'python_pipeline') {
          try {
              const events = await dashboardApi.fetchRawEvents();
              setRawData(events);
          } catch {
              setRawData(generateRawData());
          }
      } else if (dashboardData.source === 'browser_simulation') {
          setRawData(generateRawData());
      }
      // Em produção, isso viria de outra API ou do mesmo JSON
      
      setLoading(false);
    } catch (e) {
      console.error("Critical error loading telemetry", e);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, [loadData]);

  const cycleChartColor = () => {
      const currentIndex = CHART_COLORS.findIndex(c => c.value === chartColor);
      const nextIndex = (currentIndex + 1) % CHART_COLORS.length;
      setChartColor(CHART_COLORS[nextIndex].value);
  };

  // Totais para o Header
  const activeCount = data?.machines.filter(m => m.execution_state === 'ACTIVE' && m.availability === 'AVAILABLE').length || 0;
  const errorCount = data?.machines.filter(m => (m.active_alarm || m.availability === 'UNAVAILABLE')).length || 0;
  
  // Dados de tendência para o sparkline OEE
  const oeeTrendData = data?.monthly_trend.map(m => m.avg_oee * 100) || [];

  const handleDownloadCSV = () => {
      // Se a fonte for o backend Python, usa a rota de exportação direta
      if (data?.source === 'python_pipeline') {
          const backendUrl = window.location.hostname === 'localhost' 
              ? 'http://localhost:8000' 
              : `http://${window.location.hostname}:8000`;
          
          window.location.href = `${backendUrl}/demo/export`;
          return;
      }

      const csv = convertToCSV(rawData);
      if (!csv) return;
      
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `producao_fabrica_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
  };

  const handleExportChartData = (chartData: any[], filename: string) => {
      const csv = convertToCSV(chartData);
      if (!csv) return;
      
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${filename}_${new Date().toISOString().slice(0,10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-200 font-sans selection:bg-indigo-500/30">
      {/* Top Bar - HMI Style */}
      <header className="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 sticky top-0 z-50">
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
                <div className="bg-indigo-700/20 p-1.5 rounded border border-indigo-500/30">
                    <Cpu className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                    <h1 className="text-sm font-bold text-white tracking-widest uppercase">STARK TELEMETRY <span className="text-indigo-500 text-[10px]">| CNC MONITOR</span></h1>
                    <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
                        <span className="flex items-center gap-1">
                            <Wifi className={`w-3 h-3 ${data?.source === 'python_pipeline' ? 'text-emerald-500' : 'text-amber-500'}`} />
                            {data?.source === 'python_pipeline' ? 'GATEWAY: ONLINE' : 'GATEWAY: SIMULATION'}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        {/* Global Status Indicators */}
        {!loading && data && (
            <div className="hidden md:flex items-center gap-1 bg-slate-950 p-1 rounded border border-slate-800 font-mono text-xs">
                <div className="px-3 py-1 bg-slate-900 rounded flex items-center gap-2 border-r border-slate-800">
                    <Activity className="w-3 h-3 text-slate-400" />
                    <span className="text-slate-400">OEE</span>
                    <span className={`font-bold ${data.kpis.global_oee > 0.7 ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {(data.kpis.global_oee * 100).toFixed(0)}%
                    </span>
                </div>
                <div className="px-3 py-1 bg-slate-900 rounded flex items-center gap-2 border-r border-slate-800">
                    <Zap className="w-3 h-3 text-slate-400" />
                    <span className="text-slate-400">ACTIVE</span>
                    <span className="font-bold text-white">{activeCount}/{data.machines.length}</span>
                </div>
                <div className="px-3 py-1 bg-slate-900 rounded flex items-center gap-2">
                    <AlertOctagon className={`w-3 h-3 ${errorCount > 0 ? 'text-rose-500 animate-pulse' : 'text-slate-600'}`} />
                    <span className="text-slate-400">ALERTS</span>
                    <span className={`font-bold ${errorCount > 0 ? 'text-rose-400' : 'text-slate-600'}`}>{errorCount}</span>
                </div>
            </div>
        )}

        {/* Tabs & Controls */}
        <div className="flex gap-2">
            {/* Color Picker */}
            <button 
                onClick={cycleChartColor}
                className="flex items-center justify-center w-8 h-8 bg-slate-950 rounded border border-slate-800 hover:border-slate-600 transition-colors group"
                title="Change Chart Color Theme"
            >
                <Palette className="w-4 h-4 text-slate-500 group-hover:text-white" style={{ color: chartColor }} />
            </button>

            {/* Navigation */}
            <div className="flex bg-slate-950 p-1 rounded border border-slate-800">
                {[
                    { id: 'monitor', label: 'MONITOR', icon: Activity },
                    { id: 'analytics', label: 'ANALYTICS', icon: BarChart3 },
                    { id: 'data', label: 'DATA', icon: Server },
                    { id: 'codex', label: 'CODEX AI', icon: MessageSquare }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`px-3 py-1.5 text-[10px] font-bold uppercase rounded flex items-center gap-2 transition-all ${
                            activeTab === tab.id 
                            ? 'bg-slate-800 text-white shadow-sm border border-slate-700' 
                            : 'text-slate-500 hover:text-slate-300'
                        }`}
                    >
                        <tab.icon className="w-3 h-3" />
                        {tab.label}
                    </button>
                ))}
            </div>
        </div>
      </header>

      <main className="p-4 max-w-[1920px] mx-auto">
        {loading ? (
             <div className="flex h-[80vh] flex-col items-center justify-center space-y-4">
                <div className="w-12 h-12 border-2 border-slate-800 border-t-indigo-500 rounded-full animate-spin"></div>
                <p className="text-slate-600 font-mono text-xs uppercase animate-pulse">Initializing MTConnect Streams...</p>
             </div>
        ) : (
            <>
                {/* MONITOR VIEW - Grid Layout */}
                {activeTab === 'monitor' && data && (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
                        {data.machines.map(machine => (
                            <div key={machine.machine_id} className="h-[260px]">
                                <MachinePanel machine={machine} oeeTrend={oeeTrendData} chartColor={chartColor} />
                            </div>
                        ))}
                        
                        {/* Quick Stats Panel */}
                        <div className="bg-slate-900/50 border border-slate-800 border-dashed rounded-md p-4 flex flex-col justify-center gap-4 text-slate-500">
                            <div className="flex justify-between items-center">
                                <span className="text-xs uppercase">Total Parts</span>
                                <span className="text-xl font-mono text-white">{data.kpis.total_production}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs uppercase">Avg Cycle</span>
                                <span className="text-xl font-mono text-white">4m 12s</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs uppercase">Shift Eff</span>
                                <span className="text-xl font-mono text-emerald-400">92.4%</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* ANALYTICS VIEW */}
                {activeTab === 'analytics' && data && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
                        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-md p-4 h-[400px] flex flex-col">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-2">
                                    <Activity className="w-4 h-4" /> 12-Month OEE Trend
                                </h3>
                                <button 
                                    onClick={() => handleExportChartData(data.monthly_trend, 'oee_trend')}
                                    className="text-slate-500 hover:text-white transition-colors p-1"
                                    title="Export to CSV"
                                >
                                    <Download className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="flex-1 min-h-0">
                                <OeeTrendChart data={data.monthly_trend} />
                            </div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-md p-4 h-[400px] flex flex-col">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-2">
                                    <AlertOctagon className="w-4 h-4" /> Downtime Analysis
                                </h3>
                                <button 
                                    onClick={() => handleExportChartData(data.downtime_reasons, 'downtime_pareto')}
                                    className="text-slate-500 hover:text-white transition-colors p-1"
                                    title="Export to CSV"
                                >
                                    <Download className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="flex-1 min-h-0">
                                <DowntimeParetoChart data={data.downtime_reasons} />
                            </div>
                        </div>
                        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-md p-4 h-[300px] flex flex-col">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-2">
                                    <BarChart3 className="w-4 h-4" /> Real-time Machine Performance
                                </h3>
                                <button 
                                    onClick={() => handleExportChartData(data.machine_performance, 'machine_performance')}
                                    className="text-slate-500 hover:text-white transition-colors p-1"
                                    title="Export to CSV"
                                >
                                    <Download className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="flex-1 min-h-0">
                                <MachinePerformanceChart data={data.machine_performance} />
                            </div>
                        </div>
                    </div>
                )}

                {/* DATA VIEW */}
                {activeTab === 'data' && (
                    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-xl animate-in fade-in duration-300">
                        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-800/30">
                            <div className="flex items-center gap-2">
                                <Server className="w-4 h-4 text-indigo-500" />
                                <h2 className="text-sm font-bold text-white uppercase tracking-wider">Event Logs (Raw)</h2>
                            </div>
                            <button 
                                onClick={handleDownloadCSV}
                                className="text-xs flex items-center gap-1 text-slate-400 hover:text-white transition-colors bg-slate-800 px-3 py-1.5 rounded border border-slate-700"
                            >
                                <Download className="w-3 h-3" /> Export Log
                            </button>
                        </div>
                        <div className="overflow-auto max-h-[70vh]">
                            <table className="w-full text-left text-xs text-slate-400 whitespace-nowrap">
                                <thead className="bg-slate-950 text-slate-500 uppercase font-semibold sticky top-0">
                                    <tr>
                                        <th className="px-4 py-3">Timestamp</th>
                                        <th className="px-4 py-3">Machine</th>
                                        <th className="px-4 py-3">Product</th>
                                        <th className="px-4 py-3">Shift</th>
                                        <th className="px-4 py-3 text-right">Cycle (min)</th>
                                        <th className="px-4 py-3 text-right">Good</th>
                                        <th className="px-4 py-3 text-right">Scrap</th>
                                        <th className="px-4 py-3 text-right">Stop (min)</th>
                                        <th className="px-4 py-3">Stop Reason</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800 font-mono">
                                    {rawData.map((row) => (
                                        <tr key={row.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-4 py-2">{new Date(row.data).toLocaleString('pt-BR')}</td>
                                            <td className="px-4 py-2 text-indigo-400 font-bold">{row.maquina_id}</td>
                                            <td className="px-4 py-2 text-slate-300">{row.produto}</td>
                                            <td className="px-4 py-2">{row.turno}</td>
                                            <td className="px-4 py-2 text-right">{row.tempo_ciclo_min}</td>
                                            <td className="px-4 py-2 text-right text-emerald-500">{row.pecas_boas}</td>
                                            <td className="px-4 py-2 text-right text-rose-500">{row.pecas_refugo}</td>
                                            <td className="px-4 py-2 text-right">{row.parada_min}</td>
                                            <td className="px-4 py-2">
                                                {row.motivo_parada !== 'N/A' && (
                                                    <span className="px-1.5 py-0.5 bg-rose-500/10 text-rose-400 rounded text-[10px] uppercase font-bold">
                                                        {row.motivo_parada}
                                                    </span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* CODEX AI VIEW */}
                {activeTab === 'codex' && (
                    <div className="max-w-5xl mx-auto h-[calc(100vh-90px)]">
                        <CodexChat dashboardData={data as any} />
                    </div>
                )}
            </>
        )}
      </main>
    </div>
  );
};

export default App;
