import { Badge } from "../ui/badge"
import type { ReportStatus } from "../../types/report"

interface ReportStatusBadgeProps {
  status: ReportStatus
}

export const ReportStatusBadge: React.FC<ReportStatusBadgeProps> = ({ status }) => {
  const config: Record<ReportStatus, { label: string; variant: "default" | "secondary" | "success" | "destructive" | "outline" | "warning" }> = {
    pending: { label: "Đang chờ", variant: "secondary" },
    generating: { label: "Đang tạo", variant: "warning" },
    completed: { label: "Hoàn thành", variant: "success" },
    failed: { label: "Thất bại", variant: "destructive" },
  }

  const { label, variant } = config[status]

  return <Badge variant={variant}>{label}</Badge>
}
