import { Badge } from "../ui/badge"
import type { AlertSeverity } from "../../types/alert"

interface AlertSeverityBadgeProps {
  severity: AlertSeverity
}

export const AlertSeverityBadge: React.FC<AlertSeverityBadgeProps> = ({ severity }) => {
  const config: Record<AlertSeverity, { label: string; variant: "default" | "destructive" | "warning" }> = {
    low: { label: "Low", variant: "default" },
    medium: { label: "Medium", variant: "warning" },
    high: { label: "High", variant: "warning" },
    critical: { label: "Critical", variant: "destructive" },
  }

  const { label, variant } = config[severity]

  return <Badge variant={variant}>{label}</Badge>
}
