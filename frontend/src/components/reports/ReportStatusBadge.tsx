import { Badge } from "../ui/badge"
import type { ReportStatus } from "../../types/report"

interface ReportStatusBadgeProps {
  status: ReportStatus
}

export const ReportStatusBadge: React.FC<ReportStatusBadgeProps> = ({ status }) => {
  const config: Record<ReportStatus, { label: string; variant: "default" | "secondary" | "success" | "destructive" | "outline" | "warning" }> = {
    pending: { label: "Pending", variant: "secondary" },
    generating: { label: "Generating", variant: "warning" },
    completed: { label: "Completed", variant: "success" },
    failed: { label: "Failed", variant: "destructive" },
  }

  const { label, variant } = config[status]

  return <Badge variant={variant}>{label}</Badge>
}
