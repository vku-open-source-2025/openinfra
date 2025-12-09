import { useQuery } from "@tanstack/react-query"
import { incidentsApi } from "../../api/incidents"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Skeleton } from "../ui/skeleton"
import { Alert, AlertDescription } from "../ui/alert"
import { GitMerge, ChevronRight, AlertCircle, CheckCircle, Clock, ExternalLink } from "lucide-react"
import { format } from "date-fns"
import { useNavigate } from "@tanstack/react-router"
import { IncidentStatusBadge } from "./IncidentStatusBadge"
import type { Incident } from "../../types/incident"

interface IncidentHierarchyProps {
  incidentId: string
  incident: Incident
}

export const IncidentHierarchy: React.FC<IncidentHierarchyProps> = ({
  incidentId,
  incident,
}) => {
  const navigate = useNavigate()

  const { data: relatedIncidents, isLoading, error } = useQuery({
    queryKey: ["related-incidents", incidentId],
    queryFn: () => incidentsApi.getRelatedIncidents(incidentId),
    enabled: !!incidentId,
    retry: 2,
    staleTime: 30000, // Cache for 30 seconds
  })

  // Check if this incident has merged reporter IDs (indicating it's a merged incident)
  const isMergedIncident = incident.merged_reporter_ids && incident.merged_reporter_ids.length > 0
  const hasRelatedIncidents = relatedIncidents && relatedIncidents.length > 0

  if (!isMergedIncident && !hasRelatedIncidents) {
    return null // Don't show hierarchy if no related incidents
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full ml-6" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load related incidents. Please try again later.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
      <div className="flex items-center gap-2">
        <GitMerge className="h-5 w-5 text-blue-500" />
        <h3 className="text-lg font-semibold">Incident Hierarchy</h3>
        {isMergedIncident && (
          <Badge variant="secondary" className="ml-2">
            Merged from {incident.merged_reporter_ids?.length || 0} reports
          </Badge>
        )}
      </div>

      {isMergedIncident && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            This incident was created by merging {incident.merged_reporter_ids?.length || 0} duplicate reports.
            The original reports are shown below as sub-tickets.
          </AlertDescription>
        </Alert>
      )}

      {hasRelatedIncidents && (
        <div className="space-y-3">
          <div className="text-sm font-medium text-slate-700 mb-2">
            Related Incidents ({relatedIncidents.length})
          </div>
          
          {/* Main Ticket Card */}
          <div className="border-2 border-blue-300 bg-blue-50 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="default" className="bg-blue-600">
                    Main Ticket
                  </Badge>
                  <span className="font-semibold text-blue-900">{incident.title}</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-blue-700">
                  <span>#{incident.incident_number || incident.incident_code || incident.id.substring(0, 8)}</span>
                  <IncidentStatusBadge status={incident.status} severity={incident.severity} />
                  <span className="text-xs">
                    Reported {incident.created_at ? format(new Date(incident.created_at), "MMM d, yyyy HH:mm") : "Unknown"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Sub-tickets */}
          <div className="ml-6 space-y-2 border-l-2 border-slate-300 pl-4">
            {relatedIncidents.map((related) => (
              <div
                key={related.id}
                className="border border-slate-200 bg-slate-50 rounded-lg p-3 hover:bg-slate-100 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <ChevronRight className="h-4 w-4 text-slate-400" />
                      <Badge variant="outline" className="text-xs">
                        Sub-ticket
                      </Badge>
                      <span className="font-medium text-slate-900">{related.title}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-600 ml-6">
                      <span>#{related.incident_number || related.incident_code || related.id.substring(0, 8)}</span>
                      <IncidentStatusBadge status={related.status} severity={related.severity} />
                      {related.status === "resolved" && related.resolution_type === "duplicate" && (
                        <Badge variant="secondary" className="text-xs">
                          Merged
                        </Badge>
                      )}
                      <span>
                        {related.created_at ? format(new Date(related.created_at), "MMM d, yyyy HH:mm") : "Unknown"}
                      </span>
                    </div>
                    {related.description && (
                      <p className="text-xs text-slate-600 mt-1 ml-6 line-clamp-2">
                        {related.description}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate({ to: `/admin/incidents/${related.id}` })}
                    className="ml-2"
                  >
                    <ExternalLink className="h-3 w-3 mr-1" />
                    View
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!hasRelatedIncidents && isMergedIncident && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            This incident was merged from multiple reports, but the original incident details are not available.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

