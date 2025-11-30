import { Badge } from "../ui/badge"
import { Bell } from "lucide-react"

interface NotificationBadgeProps {
  count: number
  className?: string
}

export const NotificationBadge: React.FC<NotificationBadgeProps> = ({ count, className }) => {
  if (count === 0) {
    return (
      <div className={className}>
        <Bell className="h-5 w-5 text-slate-600" />
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      <Bell className="h-5 w-5 text-slate-600" />
      <Badge
        variant="destructive"
        className="absolute -top-2 -right-2 h-5 w-5 flex items-center justify-center p-0 text-xs"
      >
        {count > 99 ? "99+" : count}
      </Badge>
    </div>
  )
}
