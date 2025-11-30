import type { Notification } from "../../types/notification"
import { Badge } from "../ui/badge"
import { format } from "date-fns"
import { Bell, AlertTriangle, Wrench, FileText, DollarSign } from "lucide-react"

interface NotificationItemProps {
  notification: Notification
  onClick?: () => void
}

export const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onClick }) => {
  const iconMap = {
    alert: AlertTriangle,
    maintenance: Wrench,
    incident: FileText,
    budget: DollarSign,
    system: Bell,
  }

  const colorMap = {
    alert: "text-red-600",
    maintenance: "text-blue-600",
    incident: "text-amber-600",
    budget: "text-green-600",
    system: "text-slate-600",
  }

  const Icon = iconMap[notification.type] || Bell
  const iconColor = colorMap[notification.type] || "text-slate-600"

  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-lg border transition-colors ${
        notification.read
          ? "bg-white border-slate-200"
          : "bg-blue-50 border-blue-200"
      } ${onClick ? "cursor-pointer hover:bg-slate-50" : ""}`}
    >
      <div className="flex items-start gap-3">
        <div className={`shrink-0 ${iconColor}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className={`text-sm font-semibold ${notification.read ? "text-slate-700" : "text-slate-900"}`}>
              {notification.title}
            </h4>
            {!notification.read && (
              <Badge variant="default" className="shrink-0 text-xs">
                New
              </Badge>
            )}
          </div>
          <p className={`text-sm ${notification.read ? "text-slate-600" : "text-slate-700"}`}>
            {notification.message}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {format(new Date(notification.created_at), "MMM d, yyyy HH:mm")}
          </p>
        </div>
      </div>
    </div>
  )
}
