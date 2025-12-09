import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { incidentsApi } from "../../api/incidents"
import { Button } from "../ui/button"
import { Alert, AlertDescription } from "../ui/alert"
import { Badge } from "../ui/badge"
import { Skeleton } from "../ui/skeleton"
import { AlertTriangle, CheckCircle, XCircle, RefreshCw, GitMerge } from "lucide-react"
import { format } from "date-fns"
import { useState } from "react"

interface IncidentMergeSuggestionsProps {
  incidentId: string
  canManage: boolean // Admin or technician
}

export const IncidentMergeSuggestions: React.FC<IncidentMergeSuggestionsProps> = ({
  incidentId,
  canManage,
}) => {
  const queryClient = useQueryClient()
  const [checkingDuplicates, setCheckingDuplicates] = useState(false)

  const { data: suggestions, isLoading } = useQuery({
    queryKey: ["merge-suggestions", incidentId],
    queryFn: () => incidentsApi.getMergeSuggestions(incidentId, "pending"),
    enabled: !!incidentId,
  })

  const checkDuplicatesMutation = useMutation({
    mutationFn: () => incidentsApi.checkDuplicates(incidentId),
    onMutate: () => {
      setCheckingDuplicates(true)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["merge-suggestions", incidentId] })
    },
    onSettled: () => {
      setCheckingDuplicates(false)
    },
  })

  const approveMutation = useMutation({
    mutationFn: (suggestionId: string) => incidentsApi.approveMergeSuggestion(suggestionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", incidentId] })
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
      queryClient.invalidateQueries({ queryKey: ["merge-suggestions", incidentId] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ suggestionId, notes }: { suggestionId: string; notes?: string }) =>
      incidentsApi.rejectMergeSuggestion(suggestionId, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["merge-suggestions", incidentId] })
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  const pendingSuggestions = suggestions?.filter((s: any) => s.status === "pending") || []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Merge Suggestions</h3>
        {canManage && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => checkDuplicatesMutation.mutate()}
            disabled={checkingDuplicates}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${checkingDuplicates ? "animate-spin" : ""}`} />
            Check for Duplicates
          </Button>
        )}
      </div>

      {checkDuplicatesMutation.isSuccess && checkDuplicatesMutation.data && checkDuplicatesMutation.data.length === 0 && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>No duplicate incidents found.</AlertDescription>
        </Alert>
      )}

      {pendingSuggestions.length === 0 && !checkDuplicatesMutation.isSuccess && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            No pending merge suggestions. {canManage && "Click 'Check for Duplicates' to find potential duplicates."}
          </AlertDescription>
        </Alert>
      )}

      {pendingSuggestions.map((suggestion: any) => (
        <div
          key={suggestion.id}
          className="border border-slate-200 rounded-lg p-4 space-y-3"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <GitMerge className="h-4 w-4 text-blue-500" />
                <span className="font-semibold">Potential Duplicate Found</span>
                <Badge variant="secondary">
                  {(suggestion.similarity_score * 100).toFixed(0)}% similar
                </Badge>
              </div>
              <div className="text-sm text-slate-600 space-y-1">
                <div>
                  <strong>Duplicate Incident(s):</strong> {suggestion.duplicate_incident_ids.length} incident(s)
                </div>
                {suggestion.match_reasons && suggestion.match_reasons.length > 0 && (
                  <div>
                    <strong>Match Reasons:</strong>{" "}
                    {suggestion.match_reasons.map((reason: string) => (
                      <Badge key={reason} variant="outline" className="ml-1">
                        {reason.replace(/_/g, " ")}
                      </Badge>
                    ))}
                  </div>
                )}
                <div className="text-xs text-slate-500">
                  Suggested {format(new Date(suggestion.created_at), "MMM d, yyyy HH:mm")}
                </div>
              </div>
            </div>
          </div>

          {canManage && (
            <div className="flex gap-2 pt-2 border-t">
              <Button
                size="sm"
                variant="default"
                onClick={() => approveMutation.mutate(suggestion.id)}
                disabled={approveMutation.isPending}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve Merge
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => rejectMutation.mutate({ suggestionId: suggestion.id })}
                disabled={rejectMutation.isPending}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

