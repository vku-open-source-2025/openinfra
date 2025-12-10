import { useMemo } from "react"
import type { SensorReading } from "../../types/iot"
import { format } from "date-fns"

interface SensorChartProps {
  readings: SensorReading[]
  unit?: string
  height?: number
}

export const SensorChart: React.FC<SensorChartProps> = ({ readings, unit = "", height = 200 }) => {
  const chartData = useMemo(() => {
    if (readings.length === 0) return null

    const sortedReadings = [...readings].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    const min = Math.min(...sortedReadings.map((r) => r.value))
    const max = Math.max(...sortedReadings.map((r) => r.value))
    const range = max - min || 1

    return {
      readings: sortedReadings,
      min,
      max,
      range,
    }
  }, [readings])

  if (!chartData || chartData.readings.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 bg-slate-50 rounded-lg border border-slate-200">
        <p>Không có dữ liệu</p>
      </div>
    )
  }

  const { readings: sortedReadings, min, max, range } = chartData
  const chartHeight = height - 40
  const svgWidth = 800
  const padding = { left: 40, right: 20 }
  const chartWidth = svgWidth - padding.left - padding.right

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Phạm vi giá trị</span>
          <span className="font-semibold">
            {min.toFixed(2)} - {max.toFixed(2)} {unit}
          </span>
        </div>
      </div>
      <div className="relative" style={{ height: `${height}px` }}>
        <svg viewBox={`0 0 ${svgWidth} ${height}`} preserveAspectRatio="none" width="100%" height={height} className="overflow-visible">
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </linearGradient>
          </defs>
          <polyline
            points={sortedReadings
              .map((reading, index) => {
                const x = padding.left + (index / (sortedReadings.length - 1 || 1)) * chartWidth
                const y = chartHeight - ((reading.value - min) / range) * chartHeight + 20
                return `${x},${y}`
              })
              .join(" ")}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
          />
          <polygon
            points={`${padding.left},${chartHeight + 20} ${sortedReadings
              .map((reading, index) => {
                const x = padding.left + (index / (sortedReadings.length - 1 || 1)) * chartWidth
                const y = chartHeight - ((reading.value - min) / range) * chartHeight + 20
                return `${x},${y}`
              })
              .join(" ")} ${padding.left + chartWidth},${chartHeight + 20}`}
            fill="url(#gradient)"
          />
        </svg>
        <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-slate-500 px-2">
          <span>{format(new Date(sortedReadings[0].timestamp), "MMM d, HH:mm")}</span>
          <span>
            {format(new Date(sortedReadings[sortedReadings.length - 1].timestamp), "MMM d, HH:mm")}
          </span>
        </div>
      </div>
    </div>
  )
}
