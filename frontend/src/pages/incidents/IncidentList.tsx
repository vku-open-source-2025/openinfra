import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { incidentsApi } from "../../api/incidents"
import { IncidentCard } from "../../components/incidents/IncidentCard"
import { IncidentFilters } from "../../components/incidents/IncidentFilters"
import { Pagination } from "../../components/ui/pagination"
import { Skeleton } from "../../components/ui/skeleton"
import { Button } from "../../components/ui/button"
import { Plus } from "lucide-react"

const IncidentList: React.FC = () => {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<string>("")
  const [severity, setSeverity] = useState<string>("")
  const [search, setSearch] = useState<string>("")
  const limit = 20

  const { data: incidents, isLoading, error } = useQuery({
    queryKey: ["incidents", page, status, severity],
    queryFn: () =>
      incidentsApi.list({
        skip: (page - 1) * limit,
        limit,
        status: status || undefined,
        severity: severity || undefined,
      }),
  })

  const filteredIncidents = incidents?.filter((incident) => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      incident.title.toLowerCase().includes(searchLower) ||
      incident.description.toLowerCase().includes(searchLower) ||
      incident.location?.address?.toLowerCase().includes(searchLower) ||
      incident.asset?.name?.toLowerCase().includes(searchLower) ||
      incident.asset?.asset_code?.toLowerCase().includes(searchLower) ||
      incident.asset?.feature_type?.toLowerCase().includes(searchLower)
    )
  })

  const totalPages = incidents ? Math.ceil(incidents.length / limit) : 1

  if (error) {
    return (
      <div className="p-8 text-center text-red-500">
        Error loading incidents. Please try again.
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Incidents</h1>
          <p className="text-slate-500 mt-1">Manage and track reported incidents</p>
        </div>
        <Button onClick={() => navigate({ to: "/admin/incidents/create" })}>
          <Plus className="h-4 w-4 mr-2" />
          Report Incident
        </Button>
      </div>

      <IncidentFilters
        status={status}
        severity={severity}
        search={search}
        onStatusChange={setStatus}
        onSeverityChange={setSeverity}
        onSearchChange={setSearch}
      />

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : filteredIncidents && filteredIncidents.length > 0 ? (
        <>
          <div className="space-y-4">
            {filteredIncidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                onClick={() => navigate({ to: `/admin/incidents/${incident.id}` })}
              />
            ))}
          </div>
          {totalPages > 1 && (
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          )}
        </>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>No incidents found.</p>
        </div>
      )}
    </div>
  )
}

export default IncidentList
