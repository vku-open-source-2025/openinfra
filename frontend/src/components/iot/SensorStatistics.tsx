import type { SensorReading } from "../../types/iot"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface SensorStatisticsProps {
  readings: SensorReading[]
  unit?: string
}

export const SensorStatistics: React.FC<SensorStatisticsProps> = ({ readings, unit = "" }) => {
  if (readings.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>Không có thống kê</p>
      </div>
    )
  }

  const values = readings.map((r) => r.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const sum = values.reduce((a, b) => a + b, 0)
  const avg = sum / values.length

  const sortedValues = [...values].sort((a, b) => a - b)
  const median =
    sortedValues.length % 2 === 0
      ? (sortedValues[sortedValues.length / 2 - 1] + sortedValues[sortedValues.length / 2]) / 2
      : sortedValues[Math.floor(sortedValues.length / 2)]

  // readings are sorted newest first, so values[0] is latest, values[length-1] is oldest
  const latestValue = values[0]
  const oldestValue = values[values.length - 1]
  const trend = latestValue > oldestValue ? "up" : latestValue < oldestValue ? "down" : "stable"

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <div className="text-xs text-slate-500 mb-1">Trung bình</div>
        <div className="text-2xl font-bold text-slate-900">{avg.toFixed(2)}</div>
        <div className="text-xs text-slate-500">{unit}</div>
      </div>
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <div className="text-xs text-slate-500 mb-1">Tối thiểu</div>
        <div className="text-2xl font-bold text-slate-900">{min.toFixed(2)}</div>
        <div className="text-xs text-slate-500">{unit}</div>
      </div>
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <div className="text-xs text-slate-500 mb-1">Tối đa</div>
        <div className="text-2xl font-bold text-slate-900">{max.toFixed(2)}</div>
        <div className="text-xs text-slate-500">{unit}</div>
      </div>
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <div className="text-xs text-slate-500 mb-1">Trung vị</div>
        <div className="text-2xl font-bold text-slate-900">{median.toFixed(2)}</div>
        <div className="text-xs text-slate-500">{unit}</div>
      </div>
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <div className="text-xs text-slate-500 mb-1">Số lượng</div>
        <div className="text-2xl font-bold text-slate-900">{readings.length}</div>
        <div className="text-xs text-slate-500">readings</div>
      </div>
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <div className="text-xs text-slate-500 mb-1">Xu hướng</div>
        <div className="flex items-center gap-2">
          {trend === "up" && <TrendingUp className="h-5 w-5 text-green-600" />}
          {trend === "down" && <TrendingDown className="h-5 w-5 text-red-600" />}
          {trend === "stable" && <Minus className="h-5 w-5 text-slate-600" />}
          <span className="text-lg font-semibold text-slate-900 capitalize">{trend === 'up' ? 'Tăng' : trend === 'down' ? 'Giảm' : 'Ổn định'}</span>
        </div>
      </div>
    </div>
  )
}
