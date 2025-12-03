import { Badge } from "../ui/badge"
import type { IncidentStatus, IncidentSeverity } from "../../types/incident"

interface IncidentStatusBadgeProps {
  status: IncidentStatus
  severity?: IncidentSeverity
}

export const IncidentStatusBadge: React.FC<IncidentStatusBadgeProps> = ({ status, severity }) => {
  const statusConfig: Record<IncidentStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }> = {
    reported: { label: "Reported", variant: "secondary" },
    acknowledged: { label: "Acknowledged", variant: "default" },
    assigned: { label: "Assigned", variant: "default" },
    in_progress: { label: "In Progress", variant: "warning" },
    resolved: { label: "Resolved", variant: "success" },
    closed: { label: "Closed", variant: "outline" },
  }

  const severityConfig: Record<IncidentSeverity, { label: string; variant: "default" | "destructive" | "warning" }> = {
    low: { label: "Low", variant: "default" },
    medium: { label: "Medium", variant: "warning" },
    high: { label: "High", variant: "warning" },
    critical: { label: "Critical", variant: "destructive" },
  }

  // Safely get status info with fallback for invalid/undefined status
  const statusInfo = status && statusConfig[status as IncidentStatus]
    ? statusConfig[status as IncidentStatus]
    : { label: "Unknown", variant: "outline" as const }

  // Safely get severity info with fallback for invalid/undefined severity
  const severityInfo = severity && severityConfig[severity as IncidentSeverity]
    ? severityConfig[severity as IncidentSeverity]
    : null

  return (
    <div className="flex items-center gap-2">
      <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
      {severityInfo && (
        <Badge variant={severityInfo.variant} className="text-xs">
          {severityInfo.label}
        </Badge>
      )}
    </div>
  )
}
