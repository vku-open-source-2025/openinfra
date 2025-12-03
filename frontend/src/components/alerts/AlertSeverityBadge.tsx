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

  // Normalize severity to lowercase and ensure it's a valid key
  const normalizedSeverity = severity?.toLowerCase() as AlertSeverity
  const severityConfig = config[normalizedSeverity] || { label: severity || "Unknown", variant: "default" as const }

  const { label, variant } = severityConfig

  return <Badge variant={variant}>{label}</Badge>
}
