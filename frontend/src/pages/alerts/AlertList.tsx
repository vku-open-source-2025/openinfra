import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { alertsApi } from "../../api/alerts"
import { AlertCard } from "../../components/alerts/AlertCard"
import { AlertActions } from "../../components/alerts/AlertActions"
import { Select } from "../../components/ui/select"
import { Pagination } from "../../components/ui/pagination"
import { Skeleton } from "../../components/ui/skeleton"
import { useAuthStore } from "../../stores/authStore"

const AlertList: React.FC = () => {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<string>("")
  const [severity, setSeverity] = useState<string>("")
  const limit = 20

  const { data: alerts, isLoading } = useQuery({
    queryKey: ["alerts", "list", page, severity],
    queryFn: () =>
      alertsApi.list({
        skip: (page - 1) * limit,
        limit,
        severity: severity || undefined,
      }),
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => alertsApi.acknowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] })
    },
  })

  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      alertsApi.resolve(id, notes ? { resolution_notes: notes } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] })
    },
  })

  const dismissMutation = useMutation({
    mutationFn: (id: string) => alertsApi.dismiss(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] })
    },
  })

  const canManage = user?.role === "admin" || user?.role === "manager" || user?.role === "technician"
  const totalPages = alerts ? Math.ceil(alerts.length / limit) : 1

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tất cả cảnh báo</h1>
          <p className="text-slate-500 mt-1">Danh sách đầy đủ các cảnh báo hệ thống</p>
        </div>
      </div>

      <div className="flex gap-4">
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="Tất cả trạng thái"
        >
          <option value="">All Statuses</option>
          <option value="active">Đang hoạt động</option>
          <option value="acknowledged">Đã xác nhận</option>
          <option value="resolved">Đã giải quyết</option>
          <option value="dismissed">Đã hủy</option>
        </Select>
        <Select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          placeholder="Tất cả mức độ"
        >
          <option value="">All Severities</option>
          <option value="critical">Nguy kịch</option>
          <option value="high">Cao</option>
          <option value="medium">Trung bình</option>
          <option value="low">Thấp</option>
        </Select>
      </div>

      <div className="space-y-4">
        {alerts && alerts.length > 0 ? (
          alerts.map((alert) => (
            <div key={alert.id} className="bg-white rounded-lg border border-slate-200 p-4">
              <AlertCard alert={alert} />
              {canManage && (
                <div className="mt-4 pt-4 border-t">
                  <AlertActions
                    alert={alert}
                    onAcknowledge={async () => {
                      await acknowledgeMutation.mutateAsync(alert.id)
                    }}
                    onResolve={async (notes) => {
                      await resolveMutation.mutateAsync({ id: alert.id, notes })
                    }}
                    onDismiss={async () => {
                      await dismissMutation.mutateAsync(alert.id)
                    }}
                    canAcknowledge={canManage && alert.status === "active"}
                    canResolve={canManage && alert.status === "active"}
                    canDismiss={canManage && alert.status === "active"}
                  />
                </div>
              )}
            </div>
          ))
        ) : (
            <div className="text-center py-12 text-slate-500">
            <p>Không tìm thấy cảnh báo</p>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
      )}
    </div>
  )
}

export default AlertList
