import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { iotApi } from "../../api/iot"
import { SensorCard } from "../../components/iot/SensorCard"
import { Select } from "../../components/ui/select"
import { Input } from "../../components/ui/input"
import { Button } from "../../components/ui/button"
import { Pagination } from "../../components/ui/pagination"
import { Skeleton } from "../../components/ui/skeleton"
import { Plus } from "lucide-react"

const SensorList: React.FC = () => {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [sensorType, setSensorType] = useState<string>("")
  const [status, setStatus] = useState<string>("")
  const [search, setSearch] = useState<string>("")
  const limit = 20

  const { data: sensors, isLoading } = useQuery({
    queryKey: ["sensors", page, sensorType, status],
    queryFn: () =>
      iotApi.listSensors({
        skip: (page - 1) * limit,
        limit,
        sensor_type: sensorType || undefined,
        status: status || undefined,
      }),
  })

  const filteredSensors = sensors?.filter((sensor) => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      sensor.sensor_code.toLowerCase().includes(searchLower) ||
      sensor.sensor_type.toLowerCase().includes(searchLower)
    )
  })

  const totalPages = sensors ? Math.ceil(sensors.length / limit) : 1

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">IoT Sensors</h1>
          <p className="text-slate-500 mt-1">Manage and monitor IoT sensors</p>
        </div>
        <Button onClick={() => navigate({ to: "/admin/iot/create" })}>
          <Plus className="h-4 w-4 mr-2" />
          Register Sensor
        </Button>
      </div>

      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <Input
            placeholder="Search sensors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select
          value={sensorType}
          onChange={(e) => setSensorType(e.target.value)}
          placeholder="All Types"
        >
          <option value="">All Types</option>
          <option value="temperature">Temperature</option>
          <option value="humidity">Humidity</option>
          <option value="pressure">Pressure</option>
          <option value="vibration">Vibration</option>
          <option value="noise">Noise</option>
          <option value="air_quality">Air Quality</option>
        </Select>
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="All Statuses"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="maintenance">Maintenance</option>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : filteredSensors && filteredSensors.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSensors.map((sensor) => (
              <SensorCard
                key={sensor.id}
                sensor={sensor}
                onClick={() => navigate({ to: `/admin/iot/${sensor.id}` })}
              />
            ))}
          </div>
          {totalPages > 1 && (
            <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
          )}
        </>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>No sensors found.</p>
        </div>
      )}
    </div>
  )
}

export default SensorList
