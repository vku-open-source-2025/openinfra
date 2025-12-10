import { useQuery } from "@tanstack/react-query"
import { incidentsApi } from "../../api/incidents"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Skeleton } from "../ui/skeleton"
import { AlertCircle, FileText, Users, ChevronDown, ChevronRight } from "lucide-react"
import { format } from "date-fns"
import { useNavigate } from "@tanstack/react-router"
import { IncidentStatusBadge } from "./IncidentStatusBadge"
import type { Incident } from "../../types/incident"
import { useState } from "react"

interface IncidentHierarchyProps {
  incidentId: string
  incident: Incident
}

export const IncidentHierarchy: React.FC<IncidentHierarchyProps> = ({
  incidentId,
  incident,
}) => {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(true)

  const { data: relatedIncidents, isLoading, error } = useQuery({
    queryKey: ["related-incidents", incidentId],
    queryFn: () => incidentsApi.getRelatedIncidents(incidentId),
    enabled: !!incidentId,
    retry: 2,
    staleTime: 30000,
  })

  const isMergedIncident = incident.merged_reporter_ids && incident.merged_reporter_ids.length > 0
  const hasRelatedIncidents = relatedIncidents && relatedIncidents.length > 0

  // Only show if there are related incidents or if this is a merged incident
  if (!isMergedIncident && !hasRelatedIncidents) {
    return null
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (error) {
    return null // Fail silently
  }

  const totalReports = (incident.merged_reporter_ids?.length || 0) + (hasRelatedIncidents ? relatedIncidents.length : 0)

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      {/* Main Report */}
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-2 border-blue-400 rounded-lg p-5 mb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="bg-blue-600 text-white rounded-full p-2">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg text-blue-900">Main Report</span>
                  {totalReports > 0 && (
                    <Badge className="bg-blue-600 text-white">
                      {totalReports} {totalReports === 1 ? 'related report' : 'related reports'}
                    </Badge>
                  )}
                </div>
                <p className="text-blue-800 font-medium mt-1">{incident.title}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm text-blue-700 ml-14">
              <span>#{incident.incident_number || incident.incident_code || incident.id.substring(0, 8)}</span>
              <IncidentStatusBadge status={incident.status} severity={incident.severity} />
              {incident.created_at && (
                <span>{format(new Date(incident.created_at), "MMM d, yyyy")}</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Related Reports */}
      {hasRelatedIncidents && (
        <div className="space-y-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 font-medium text-sm w-full transition-colors"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            <Users className="h-4 w-4" />
            <span>Same Issue Reports ({relatedIncidents.length})</span>
          </button>

          {expanded && (
            <div className="space-y-2 pl-6 border-l-2 border-slate-300">
              {relatedIncidents.map((related) => (
                <div
                  key={related.id}
                  className="bg-slate-50 border border-slate-200 rounded-lg p-4 hover:bg-slate-100 hover:border-slate-300 transition-all cursor-pointer"
                  onClick={() => navigate({ to: `/admin/incidents/${related.id}` })}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 bg-slate-400 rounded-full flex-shrink-0 mt-1.5"></div>
                        <span className="font-medium text-slate-900">{related.title}</span>
                        {related.status === "resolved" && related.resolution_type === "duplicate" && (
                          <Badge variant="secondary" className="text-xs">Already Merged</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-600 ml-4 flex-wrap">
                        <span>#{related.incident_number || related.incident_code || related.id.substring(0, 8)}</span>
                        <IncidentStatusBadge status={related.status} severity={related.severity} />
                        {related.created_at && (
                          <span>{format(new Date(related.created_at), "MMM d, yyyy")}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
