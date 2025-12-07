import { Badge } from "../ui/badge"
import type { SensorStatus } from "../../types/iot"

interface SensorStatusBadgeProps {
  status: SensorStatus
  lastSeen?: string
}

export const SensorStatusBadge: React.FC<SensorStatusBadgeProps> = ({ status, lastSeen }) => {
  const getStatusInfo = () => {
    if (status === "active" || status === "online") {
      if (lastSeen) {
        const lastSeenDate = new Date(lastSeen)
        const now = new Date()
        const minutesAgo = Math.floor((now.getTime() - lastSeenDate.getTime()) / 60000)

        if (minutesAgo > 30) {
          return { label: "Offline", variant: "destructive" as const }
        }
        if (minutesAgo > 10) {
          return { label: "Warning", variant: "warning" as const }
        }
      }
      return { label: "Online", variant: "success" as const }
    }
    if (status === "maintenance") {
      return { label: "Maintenance", variant: "warning" as const }
    }
    if (status === "offline") {
      return { label: "Offline", variant: "destructive" as const }
    }
    if (status === "error") {
      return { label: "Error", variant: "destructive" as const }
    }
    return { label: "Inactive", variant: "outline" as const }
  }

  const { label, variant } = getStatusInfo()

  return <Badge variant={variant}>{label}</Badge>
}
