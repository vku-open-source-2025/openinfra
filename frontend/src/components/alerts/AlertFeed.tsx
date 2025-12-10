import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { alertsApi } from "../../api/alerts"
import { AlertCard } from "./AlertCard"
import { Skeleton } from "../ui/skeleton"
import { AlertTriangle } from "lucide-react"

interface AlertFeedProps {
  limit?: number
  severity?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export const AlertFeed: React.FC<AlertFeedProps> = ({
  limit = 10,
  severity,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}) => {
  const [refetchInterval, setRefetchInterval] = useState<number | false>(autoRefresh ? refreshInterval : false)

  const { data: alerts, isLoading } = useQuery({
    queryKey: ["alerts", "feed", severity, limit],
    queryFn: () =>
      alertsApi.list({
        limit,
        status: "active",
        severity: severity || undefined,
      }),
    refetchInterval,
  })

  const activeAlerts = alerts?.filter((alert) => alert.status === "active") || []

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    )
  }

  if (activeAlerts.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-slate-400" />
        <p>Không có cảnh báo hoạt động</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {activeAlerts.map((alert) => (
        <AlertCard key={alert.id} alert={alert} />
      ))}
    </div>
  )
}
