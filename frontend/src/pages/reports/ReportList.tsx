import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { reportsApi } from "../../api/reports"
import { ReportCard } from "../../components/reports/ReportCard"
import { Select } from "../../components/ui/select"
import { Pagination } from "../../components/ui/pagination"
import { Skeleton } from "../../components/ui/skeleton"

const ReportList: React.FC = () => {
  const [page, setPage] = useState(1)
  const [type, setType] = useState<string>("")
  const [status, setStatus] = useState<string>("")
  const limit = 20

  const { data: reports, isLoading } = useQuery({
    queryKey: ["reports", page, type, status],
    queryFn: () =>
      reportsApi.list({
        skip: (page - 1) * limit,
        limit,
        type: type || undefined,
        status: status || undefined,
      }),
  })

  // Poll for generating reports
  const generatingReports = reports?.filter((r) => r.status === "generating") || []
  useEffect(() => {
    if (generatingReports.length > 0) {
      const interval = setInterval(() => {
        // Refetch reports to check status
        window.location.reload()
      }, 5000) // Poll every 5 seconds
      return () => clearInterval(interval)
    }
  }, [generatingReports.length])

  const handleDownload = async (reportId: string) => {
    try {
      const { file_url } = await reportsApi.download(reportId)
      if (file_url) {
        window.open(file_url, "_blank")
      }
    } catch (error) {
      console.error("Failed to download report:", error)
    }
  }

  const totalPages = reports ? Math.ceil(reports.length / limit) : 1

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Báo cáo</h1>
        <p className="text-slate-500 mt-1">Xem và tải xuống các báo cáo đã tạo</p>
      </div>

      <div className="flex gap-4">
        <Select
          value={type}
          onChange={(e) => setType(e.target.value)}
          placeholder="Tất cả loại"
        >
          <option value="">All Types</option>
          <option value="maintenance">Bảo trì</option>
          <option value="budget">Ngân sách</option>
          <option value="incident">Sự cố</option>
          <option value="asset">Tài sản</option>
        </Select>
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="Tất cả trạng thái"
        >
          <option value="">All Statuses</option>
          <option value="pending">Đang chờ</option>
          <option value="generating">Đang tạo</option>
          <option value="completed">Hoàn thành</option>
          <option value="failed">Thất bại</option>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : reports && reports.length > 0 ? (
        <>
          <div className="space-y-4">
            {reports.map((report) => (
              <ReportCard
                key={report.id}
                report={report}
                onDownload={() => handleDownload(report.id)}
              />
            ))}
          </div>
          {totalPages > 1 && (
            <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
          )}
        </>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>Không tìm thấy báo cáo.</p>
        </div>
      )}
    </div>
  )
}

export default ReportList
