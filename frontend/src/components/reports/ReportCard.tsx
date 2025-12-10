import { ReportStatusBadge } from "./ReportStatusBadge"
import type { Report } from "../../types/report"
import { FileText, Download } from "lucide-react"
import { format } from "date-fns"
import { Button } from "../ui/button"

interface ReportCardProps {
  report: Report
  onDownload?: () => void
}

export const ReportCard: React.FC<ReportCardProps> = ({ report, onDownload }) => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3 flex-1">
          <div className="bg-blue-100 p-2 rounded-lg">
            <FileText className="h-5 w-5 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-slate-900 mb-1">{report.report_code}</h3>
            <p className="text-sm text-slate-600 capitalize">Báo cáo {report.type}</p>
            <p className="text-xs text-slate-500 mt-1">
              Tạo lúc {format(new Date(report.created_at), "MMM d, yyyy HH:mm")}
            </p>
          </div>
        </div>
        <ReportStatusBadge status={report.status} />
      </div>

      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-500">
          Format: <span className="font-medium uppercase">{report.format}</span>
        </div>
        {report.status === "completed" && report.file_url && onDownload && (
            <Button size="sm" variant="outline" onClick={onDownload}>
            <Download className="h-3 w-3 mr-1" />
            Tải xuống
          </Button>
        )}
      </div>

      {report.status === "generating" && (
        <div className="mt-3 pt-3 border-t">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span>Đang tạo báo cáo...</span>
          </div>
        </div>
      )}
    </div>
  )
}
