import { useQuery } from "@tanstack/react-query"
import { useParams, useNavigate, Link } from "@tanstack/react-router"
import { iotApi } from "../../api/iot"
import { assetsApi } from "../../api/assets"
import { SensorStatusBadge } from "../../components/iot/SensorStatusBadge"
import { SensorChart } from "../../components/iot/SensorChart"
import { SensorStatistics } from "../../components/iot/SensorStatistics"
import { Button } from "../../components/ui/button"
import { Skeleton } from "../../components/ui/skeleton"
import { DatePicker } from "../../components/ui/date-picker"
import { ArrowLeft, Calendar, MapPin, ExternalLink } from "lucide-react"
import { useState } from "react"
import { format, subDays } from "date-fns"

const SensorDetail: React.FC = () => {
  const { id } = useParams({ from: "/admin/iot/$id" })
  const navigate = useNavigate()
  const [dateRange, setDateRange] = useState({
    from: subDays(new Date(), 7),
    to: new Date(),
  })

  const { data: sensor, isLoading: sensorLoading } = useQuery({
    queryKey: ["sensor", id],
    queryFn: () => iotApi.getSensorById(id),
  })

  const { data: readings, isLoading: readingsLoading } = useQuery({
    queryKey: ["sensor-readings", id, dateRange.from, dateRange.to],
    queryFn: () =>
      iotApi.getSensorData(id, {
        from_time: dateRange.from.toISOString(),
        to_time: dateRange.to.toISOString(),
        limit: 1000,
      }),
    enabled: !!sensor,
  })

  const { data: statistics } = useQuery({
    queryKey: ["sensor-statistics", id, dateRange.from, dateRange.to],
    queryFn: () =>
      iotApi.getSensorStatistics(id, {
        from_time: dateRange.from.toISOString(),
        to_time: dateRange.to.toISOString(),
        granularity: "hour",
      }),
    enabled: !!sensor,
  })

  // Fetch linked asset
  const { data: linkedAsset } = useQuery({
    queryKey: ["sensor-asset", sensor?.asset_id],
    queryFn: () => assetsApi.getById(sensor!.asset_id),
    enabled: !!sensor?.asset_id,
  })

  if (sensorLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!sensor) {
    return (
      <div className="p-6 text-center text-red-500">
        Sensor not found.
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/iot" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Sensors
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">{sensor.sensor_code}</h1>
            <p className="text-slate-600">{sensor.sensor_type}</p>
          </div>
          <SensorStatusBadge status={sensor.status} lastSeen={sensor.last_seen} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-1">Last Reading</h3>
            <p className="text-2xl font-bold text-slate-900">
              {sensor.last_reading !== undefined
                ? `${sensor.last_reading} ${sensor.measurement_unit || ""}`
                : "N/A"}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-1">Last Seen</h3>
            <p className="text-lg text-slate-900">
              {sensor.last_seen
                ? format(new Date(sensor.last_seen), "MMM d, yyyy HH:mm")
                : "Never"}
            </p>
          </div>
        </div>

        {/* Linked Asset */}
        {linkedAsset && (
          <div className="border-t border-slate-200 pt-4 mt-4">
            <h3 className="text-sm font-medium text-slate-500 mb-2">Linked Asset</h3>
            <Link
              to={`/admin/assets/${linkedAsset.id}`}
              className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="font-medium text-slate-900">{linkedAsset.name || linkedAsset.feature_type}</p>
                  <p className="text-sm text-slate-500">{linkedAsset.feature_code}</p>
                </div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-400" />
            </Link>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Data Visualization</h2>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-500" />
            <DatePicker
              value={dateRange.from}
              onChange={(date) => date && setDateRange({ ...dateRange, from: date })}
            />
            <span className="text-slate-500">to</span>
            <DatePicker
              value={dateRange.to}
              onChange={(date) => date && setDateRange({ ...dateRange, to: date })}
            />
          </div>
        </div>

        {readingsLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : readings && readings.length > 0 ? (
          <>
            <SensorChart readings={readings} unit={sensor.measurement_unit} />
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-4">Statistics</h3>
              <SensorStatistics readings={readings} unit={sensor.measurement_unit} />
            </div>
          </>
        ) : (
          <div className="text-center py-12 text-slate-500">
            <p>No data available for the selected date range</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default SensorDetail
