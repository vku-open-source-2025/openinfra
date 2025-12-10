import type { Maintenance } from "../../types/maintenance";
import {
    MapPin,
    Clock,
    User,
    Wrench,
    CheckCircle,
    AlertCircle,
    Calendar,
    XCircle,
} from "lucide-react";
import { format } from "date-fns";
import { Badge } from "../ui/badge";

interface MaintenanceCardProps {
    maintenance: Maintenance;
    onClick?: () => void;
}

export const MaintenanceCard: React.FC<MaintenanceCardProps> = ({
    maintenance,
    onClick,
}) => {
    const getStatusConfig = () => {
        switch (maintenance.status) {
            case "scheduled":
                return {
                    icon: Calendar,
                    color: "text-blue-600",
                    bgColor: "bg-blue-50",
                    borderColor: "border-blue-200",
                    label: "Scheduled",
                };
            case "in_progress":
                return {
                    icon: Wrench,
                    color: "text-orange-600",
                    bgColor: "bg-orange-50",
                    borderColor: "border-orange-200",
                    label: "In Progress",
                };
            case "completed":
                return {
                    icon: CheckCircle,
                    color: "text-green-600",
                    bgColor: "bg-green-50",
                    borderColor: "border-green-200",
                    label: "Completed",
                };
            case "cancelled":
                return {
                    icon: XCircle,
                    color: "text-red-600",
                    bgColor: "bg-red-50",
                    borderColor: "border-red-200",
                    label: "Cancelled",
                };
            default:
                return {
                    icon: Clock,
                    color: "text-slate-600",
                    bgColor: "bg-slate-50",
                    borderColor: "border-slate-200",
                    label: maintenance.status,
                };
        }
    };

    const getPriorityConfig = () => {
        switch (maintenance.priority) {
            case "urgent":
                return { variant: "destructive" as const, label: "Urgent" };
            case "high":
                return { variant: "destructive" as const, label: "High" };
            case "medium":
                return { variant: "warning" as const, label: "Medium" };
            case "low":
                return { variant: "default" as const, label: "Low" };
            default:
                return {
                    variant: "default" as const,
                    label: maintenance.priority,
                };
        }
    };

    const statusConfig = getStatusConfig();
    const priorityConfig = getPriorityConfig();
    const StatusIcon = statusConfig.icon;

    return (
        <div
            onClick={onClick}
            className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
        >
            <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-slate-900">
                            {maintenance.title}
                        </h3>
                        <Badge
                            variant={priorityConfig.variant}
                            className="text-xs"
                        >
                            {priorityConfig.label}
                        </Badge>
                    </div>
                    <p className="text-sm text-slate-600 mb-2 line-clamp-2">
                        {maintenance.description}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
                        <span className="font-medium">
                            WO: {maintenance.work_order_number}
                        </span>
                        {maintenance.type && (
                            <span className="px-1.5 py-0.5 bg-slate-100 rounded capitalize">
                                {maintenance.type}
                            </span>
                        )}
                    </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                    <div
                        className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}
                    >
                        <StatusIcon className="h-3.5 w-3.5" />
                        <span>{statusConfig.label}</span>
                    </div>
                </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-3 pt-3 border-t border-slate-100">
                <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    <span>
                        Scheduled:{" "}
                        {format(
                            new Date(maintenance.scheduled_date),
                            "MMM d, yyyy"
                        )}
                    </span>
                </div>
                {maintenance.started_at && (
                    <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>
                            Started:{" "}
                            {format(
                                new Date(maintenance.started_at),
                                "MMM d, yyyy HH:mm"
                            )}
                        </span>
                    </div>
                )}
                {maintenance.completed_at && (
                    <div className="flex items-center gap-1 text-green-600">
                        <CheckCircle className="h-3 w-3" />
                        <span>
                            Completed:{" "}
                            {format(
                                new Date(maintenance.completed_at),
                                "MMM d, yyyy"
                            )}
                        </span>
                    </div>
                )}
                {maintenance.estimated_cost && (
                    <div className="flex items-center gap-1">
                        <span className="font-medium">
                            Est. Cost: ${maintenance.estimated_cost.toFixed(2)}
                        </span>
                    </div>
                )}
                {maintenance.actual_cost && (
                    <div className="flex items-center gap-1 text-green-600">
                        <span className="font-medium">
                            Actual: ${maintenance.actual_cost.toFixed(2)}
                        </span>
                    </div>
                )}
            </div>

            {maintenance.approval_status === "pending" && (
                <div className="mt-2 pt-2 border-t border-yellow-200">
                    <div className="flex items-center gap-1 text-xs text-yellow-700 bg-yellow-50 px-2 py-1 rounded">
                        <AlertCircle className="h-3 w-3" />
                        <span>Cost approval pending</span>
                    </div>
                </div>
            )}
        </div>
    );
};
