import { SensorStatusBadge } from "./SensorStatusBadge"
import type { IoTSensor } from "../../types/iot"
import { Activity, MapPin } from "lucide-react"

interface SensorCardProps {
  sensor: IoTSensor
  onClick?: () => void
}

export const SensorCard: React.FC<SensorCardProps> = ({ sensor, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900 mb-1">{sensor.sensor_code}</h3>
          <p className="text-sm text-slate-600 mb-2">{sensor.sensor_type}</p>
        </div>
        <SensorStatusBadge status={sensor.status} lastSeen={sensor.last_seen} />
      </div>
      <div className="flex items-center gap-4 text-xs text-slate-500">
        {sensor.last_reading !== undefined && (
          <div className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            <span>
              {sensor.last_reading} {sensor.measurement_unit || ""}
            </span>
          </div>
        )}
        {sensor.last_seen && (
          <div className="flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            <span>Seen {new Date(sensor.last_seen).toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  )
}
