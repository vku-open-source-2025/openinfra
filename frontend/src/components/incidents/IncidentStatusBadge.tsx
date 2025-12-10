import { Badge } from "../ui/badge";
import type { IncidentStatus, IncidentSeverity } from "../../types/incident";

interface IncidentStatusBadgeProps {
    status: IncidentStatus;
    severity?: IncidentSeverity;
}

export const IncidentStatusBadge: React.FC<IncidentStatusBadgeProps> = ({
    status,
    severity,
}) => {
    const statusConfig: Record<
        IncidentStatus,
        {
            label: string;
            variant:
                | "default"
                | "secondary"
                | "destructive"
                | "outline"
                | "success"
                | "warning";
        }
    > = {
        reported: { label: "Đã báo cáo", variant: "secondary" },
        acknowledged: { label: "Đã nhận", variant: "default" },
        assigned: { label: "Đã phân công", variant: "default" },
        investigating: { label: "Đang điều tra", variant: "warning" },
        in_progress: { label: "Đang thực hiện", variant: "warning" },
        waiting_approval: { label: "Đang chờ phê duyệt", variant: "warning" },
        resolved: { label: "Đã xử lý", variant: "success" },
        closed: { label: "Đã đóng", variant: "outline" },
    };

    const severityConfig: Record<
        IncidentSeverity,
        { label: string; variant: "default" | "destructive" | "warning" }
    > = {
        low: { label: "Thấp", variant: "default" },
        medium: { label: "Trung bình", variant: "warning" },
        high: { label: "Cao", variant: "warning" },
        critical: { label: "Nghiêm trọng", variant: "destructive" },
    };

    // Safely get status info with fallback for invalid/undefined status
    const statusInfo =
        status && statusConfig[status as IncidentStatus]
            ? statusConfig[status as IncidentStatus]
            : { label: "Không xác định", variant: "outline" as const };

    // Safely get severity info with fallback for invalid/undefined severity
    const severityInfo =
        severity && severityConfig[severity as IncidentSeverity]
            ? severityConfig[severity as IncidentSeverity]
            : null;

    return (
        <div className="flex items-center gap-2">
            <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
            {severityInfo && (
                <Badge variant={severityInfo.variant} className="text-xs">
                    {severityInfo.label}
                </Badge>
            )}
        </div>
    );
};
