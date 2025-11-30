import { AlertSeverityBadge } from "./AlertSeverityBadge"
import type { Alert } from "../../types/alert"
import { Clock, MapPin } from "lucide-react"
import { format } from "date-fns"
import { Badge } from "../ui/badge"

interface AlertCardProps {
  alert: Alert
  onClick?: () => void
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert, onClick }) => {
  const statusConfig: Record<typeof alert.status, { label: string; variant: "default" | "secondary" | "success" | "outline" }> = {
    active: { label: "Active", variant: "default" },
    acknowledged: { label: "Acknowledged", variant: "secondary" },
    resolved: { label: "Resolved", variant: "success" },
    dismissed: { label: "Dismissed", variant: "outline" },
  }

  const statusInfo = statusConfig[alert.status]

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-lg border p-4 hover:shadow-md transition-shadow ${
        onClick ? "cursor-pointer" : ""
      } ${alert.status === "active" && alert.severity === "critical" ? "border-red-300 bg-red-50" : ""}`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900 mb-1">{alert.message}</h3>
          <p className="text-xs text-slate-500 mb-2">{alert.alert_type}</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <AlertSeverityBadge severity={alert.severity} />
          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
        </div>
      </div>
      <div className="flex items-center gap-4 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>{format(new Date(alert.created_at), "MMM d, yyyy HH:mm")}</span>
        </div>
        {alert.asset_id && (
          <div className="flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            <span>Asset #{alert.asset_id.slice(-6)}</span>
          </div>
        )}
      </div>
    </div>
  )
}
