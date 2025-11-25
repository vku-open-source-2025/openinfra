import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatsCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    trend?: string;
    trendUp?: boolean;
    color: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, trend, trendUp, color }) => {
    return (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
                    <h3 className="text-2xl font-bold text-slate-900">{value}</h3>
                </div>
                <div className={`p-3 rounded-lg ${color} bg-opacity-10`}>
                    <Icon className={color.replace('bg-', 'text-')} size={24} />
                </div>
            </div>
            {trend && (
                <div className="mt-4 flex items-center gap-2 text-sm">
                    <span className={trendUp ? 'text-green-600' : 'text-red-600'}>
                        {trendUp ? '↑' : '↓'} {trend}
                    </span>
                    <span className="text-slate-400">vs last month</span>
                </div>
            )}
        </div>
    );
};

export default StatsCard;
