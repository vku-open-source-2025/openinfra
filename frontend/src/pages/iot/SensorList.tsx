import { useState, useEffect } from "react"
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
  const itemsPerPage = 20

  // Reset page when filters change
  useEffect(() => {
    setPage(1)
  }, [sensorType, status, search])

  // Fetch all sensors (with high limit) for client-side pagination
  const { data: allSensors, isLoading } = useQuery({
    queryKey: ["sensors", sensorType, status],
    queryFn: () =>
      iotApi.listSensors({
        skip: 0,
        limit: 2000, // Get all sensors
        sensor_type: sensorType || undefined,
        status: status || undefined,
      }),
  })

  // Filter sensors by search term
  const filteredSensors = allSensors?.filter((sensor) => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      sensor.sensor_code.toLowerCase().includes(searchLower) ||
      sensor.sensor_type.toLowerCase().includes(searchLower)
    )
  })

  // Calculate pagination
  const totalItems = filteredSensors?.length || 0
  const totalPages = Math.ceil(totalItems / itemsPerPage)
  
  // Get current page items
  const paginatedSensors = filteredSensors?.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  )

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
      ) : paginatedSensors && paginatedSensors.length > 0 ? (
        <>
          <div className="text-sm text-slate-500 mb-2">
            Showing {(page - 1) * itemsPerPage + 1}-{Math.min(page * itemsPerPage, totalItems)} of {totalItems} sensors
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {paginatedSensors.map((sensor) => (
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
