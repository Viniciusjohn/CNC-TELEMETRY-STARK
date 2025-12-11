import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral' | 'danger';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, subValue, trend }) => {
  let trendColor = 'text-slate-400';
  if (trend === 'up') trendColor = 'text-emerald-400';
  if (trend === 'down') trendColor = 'text-rose-400';
  if (trend === 'danger') trendColor = 'text-amber-400';

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 shadow-lg relative overflow-hidden group">
      <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
        <Icon className="w-16 h-16 text-slate-200" />
      </div>
      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-slate-700 rounded-md">
                <Icon className="w-5 h-5 text-blue-400" />
            </div>
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest">{title}</h3>
        </div>
        <div className="flex flex-col mt-2">
          <span className="text-3xl font-bold text-white tracking-tight">{value}</span>
          {subValue && (
            <span className={`text-xs mt-1 font-medium ${trendColor}`}>
              {subValue}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatsCard;