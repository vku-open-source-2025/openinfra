import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMaintenanceLogs } from '../api';
import { Clock, CheckCircle, AlertCircle, Calendar } from 'lucide-react';

interface MaintenanceLogListProps {
    assetId: string;
}

const MaintenanceLogList: React.FC<MaintenanceLogListProps> = ({ assetId }) => {
    const { data: logs, isLoading, error } = useQuery({
        queryKey: ['maintenance', assetId],
        queryFn: () => getMaintenanceLogs(assetId),
        enabled: !!assetId,
    });

    if (isLoading) return <div className="text-sm text-slate-500 py-4">Loading history...</div>;
    if (error) return <div className="text-sm text-red-500 py-4">Error loading history</div>;
    if (!logs || logs.length === 0) return <div className="text-sm text-slate-400 py-4 italic">No maintenance history found.</div>;

    return (
        <div className="relative border-l-2 border-slate-200 ml-3 space-y-6 py-2">
            {logs.map((log) => {
                let StatusIcon = Clock;
                let statusColor = "text-slate-500 bg-slate-100";

                if (log.status === 'Completed') {
                    StatusIcon = CheckCircle;
                    statusColor = "text-green-600 bg-green-100";
                } else if (log.status === 'In Progress') {
                    StatusIcon = Calendar;
                    statusColor = "text-blue-600 bg-blue-100";
                } else if (log.status === 'Pending') {
                    StatusIcon = AlertCircle;
                    statusColor = "text-amber-600 bg-amber-100";
                }

                return (
                    <div key={log._id} className="relative pl-6">
                        <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full border-2 border-white ${statusColor.split(' ')[1]}`}></div>
                        <div className="bg-white rounded-lg border border-slate-100 p-3 shadow-sm">
                            <div className="flex justify-between items-start mb-1">
                                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${statusColor} flex items-center gap-1`}>
                                    <StatusIcon size={12} />
                                    {log.status}
                                </span>
                                <span className="text-xs text-slate-400">
                                    {new Date(log.scheduled_date).toLocaleDateString()}
                                </span>
                            </div>
                            <p className="text-sm font-medium text-slate-800 mb-1">{log.description}</p>
                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                <span>Tech: {log.technician}</span>
                                {(log as any).approval_status && (
                                    <span className={`px-2 py-0.5 rounded text-xs ${
                                        (log as any).approval_status === "approved" ? "bg-green-100 text-green-700" :
                                        (log as any).approval_status === "rejected" ? "bg-red-100 text-red-700" :
                                        "bg-yellow-100 text-yellow-700"
                                    }`}>
                                        {(log as any).approval_status}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default MaintenanceLogList;
