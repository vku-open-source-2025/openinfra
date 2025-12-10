import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { iotApi } from "../../api/iot"
import { SensorStatusBadge } from "../iot/SensorStatusBadge"
import { Skeleton } from "../ui/skeleton"
import { Activity, ExternalLink } from "lucide-react"
import { format } from "date-fns"

interface AssetSensorsTabProps {
  assetId: string
}

const AssetSensorsTab: React.FC<AssetSensorsTabProps> = ({ assetId }) => {
  const navigate = useNavigate()

  const { data: sensors, isLoading } = useQuery({
    queryKey: ["asset-sensors", assetId],
    queryFn: () => iotApi.listSensors({ asset_id: assetId, limit: 100 }),
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    )
  }

  if (!sensors || sensors.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <Activity className="h-12 w-12 mx-auto mb-4 text-slate-300" />
        <p className="text-lg font-medium mb-2">Chưa kết nối cảm biến</p>
        <p className="text-sm">Tài sản này chưa có cảm biến IoT liên kết.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold">Cảm biến đã kết nối ({sensors.length})</h3>
      </div>

      <div className="grid gap-4">
        {sensors.map((sensor) => (
          <div
            key={sensor.id}
            onClick={() => navigate({ to: `/admin/iot/${sensor.id}` })}
            className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold text-slate-900">{sensor.sensor_code}</h4>
                  <SensorStatusBadge status={sensor.status} lastSeen={sensor.last_seen} />
                </div>
                <p className="text-sm text-slate-600 mb-2">{sensor.sensor_type}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Lần đọc cuối:</span>
                    <span className="ml-2 font-medium">
                      {sensor.last_reading != null
                        ? `${typeof sensor.last_reading === 'object' 
                            ? (sensor.last_reading as { value?: number })?.value 
                            : sensor.last_reading} ${sensor.measurement_unit || ''}`
                        : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Đơn vị:</span>
                    <span className="ml-2 font-medium">{sensor.measurement_unit || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Tần suất mẫu:</span>
                    <span className="ml-2 font-medium">{sensor.sample_rate ? `${sensor.sample_rate}s` : 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Lần xuất hiện cuối:</span>
                    <span className="ml-2 font-medium">
                      {sensor.last_seen
                        ? format(new Date(sensor.last_seen), "MMM d, HH:mm")
                        : 'Chưa từng'}
                    </span>
                  </div>
                </div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-400" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AssetSensorsTab
