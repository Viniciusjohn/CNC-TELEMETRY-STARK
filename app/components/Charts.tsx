
import React from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  BarChart, Bar, Cell, AreaChart, Area
} from 'recharts';
import { MonthlyMetric, MachineMetric, DowntimeMetric } from '../types';

interface OeeTrendProps { data: MonthlyMetric[]; }
interface MachineProps { data: MachineMetric[]; }
interface DowntimeProps { data: DowntimeMetric[]; }
interface SparklineProps { data: number[]; color?: string; }

const CustomTooltip = ({ active, payload, label, unit = '' }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-600 p-2 rounded shadow-2xl z-50">
        <p className="text-slate-300 text-xs font-bold mb-1">{label}</p>
        <p className="text-white text-sm font-mono">
          {payload[0].value.toFixed(1)}{unit}
        </p>
      </div>
    );
  }
  return null;
};

export const LoadSparkline: React.FC<SparklineProps> = ({ data, color = "#6366f1" }) => {
    const formattedData = data.map((val, i) => ({ i, val }));
    
    // Gradiente dinâmico baseado na cor
    const gradientId = `colorLoad-${color.replace('#', '')}`;
    
    return (
        <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formattedData}>
                <defs>
                    <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={color} stopOpacity={0}/>
                    </linearGradient>
                </defs>
                <YAxis hide domain={[0, 100]} /> {/* Fixado em 0-100% para realismo */}
                <Area 
                    type="monotone" 
                    dataKey="val" 
                    stroke={color} 
                    fillOpacity={1} 
                    fill={`url(#${gradientId})`} 
                    strokeWidth={2}
                    isAnimationActive={false} // Performance optimization for realtime
                />
            </AreaChart>
        </ResponsiveContainer>
    );
};

export const OeeTrendChart: React.FC<OeeTrendProps> = ({ data }) => {
  if (!data || data.length === 0) return null;
  const formattedData = data.map(d => ({...d, oee_percent: d.avg_oee * 100}));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
        <XAxis 
          dataKey="month" 
          stroke="#94a3b8" 
          tick={{ fill: '#94a3b8', fontSize: 11 }} 
          tickLine={false}
          axisLine={false}
        />
        <YAxis 
          stroke="#94a3b8" 
          tick={{ fill: '#94a3b8', fontSize: 11 }} 
          tickFormatter={(val) => `${val}%`}
          domain={[40, 100]}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip unit="%" />} cursor={{ stroke: '#475569', strokeWidth: 1 }} />
        <Line 
          type="monotone" 
          dataKey="oee_percent" 
          name="OEE"
          stroke="#10b981" 
          strokeWidth={3} 
          dot={{ r: 3, fill: '#0f172a', stroke: '#10b981', strokeWidth: 2 }} 
          activeDot={{ r: 5, fill: '#34d399' }} 
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export const MachinePerformanceChart: React.FC<MachineProps> = ({ data }) => {
  if (!data || data.length === 0) return null;
  // Slice top 8 and convert to percentage
  const formattedData = data.slice(0, 8).map(d => ({ ...d, oee_percent: d.oee * 100 }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={formattedData} layout="vertical" margin={{ top: 0, right: 20, left: 20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={true} vertical={false} />
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis 
          dataKey="maquina_id" 
          type="category" 
          width={60} 
          tick={{ fill: '#e2e8f0', fontSize: 11, fontWeight: 600 }} 
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip unit="%" />} cursor={{ fill: '#334155', opacity: 0.2 }} />
        <Bar dataKey="oee_percent" radius={[0, 4, 4, 0]} barSize={18}>
          {formattedData.map((entry, index) => (
            <Cell 
                key={`cell-${index}`} 
                fill={entry.oee_percent > 80 ? '#10b981' : entry.oee_percent > 60 ? '#f59e0b' : '#ef4444'} 
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export const DowntimeParetoChart: React.FC<DowntimeProps> = ({ data }) => {
    if (!data || data.length === 0) return null;
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis 
            dataKey="motivo" 
            stroke="#94a3b8" 
            tick={{ fill: '#94a3b8', fontSize: 10 }} 
            tickLine={false}
            axisLine={false}
            interval={0}
            angle={-25}
            textAnchor="end"
            height={50}
          />
          <YAxis 
             stroke="#94a3b8" 
             tick={{ fill: '#94a3b8', fontSize: 11 }}
             tickLine={false}
             axisLine={false}
          />
          <Tooltip content={<CustomTooltip unit=" min" />} cursor={{ fill: '#334155', opacity: 0.2 }} />
          <Bar dataKey="minutos" fill="#f43f5e" radius={[4, 4, 0, 0]} barSize={30} />
        </BarChart>
      </ResponsiveContainer>
    );
  };
