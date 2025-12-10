import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { incidentsApi } from "../../api/incidents"
import { Button } from "../ui/button"
import { Badge } from "../ui/badge"
import { Skeleton } from "../ui/skeleton"
import { RefreshCw, GitMerge, CheckCircle, XCircle, AlertCircle } from "lucide-react"
import { useState } from "react"

interface IncidentMergeSuggestionsProps {
  incidentId: string
  canManage: boolean
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
    mutationFn: ({ suggestionId }: { suggestionId: string }) =>
      incidentsApi.rejectMergeSuggestion(suggestionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["merge-suggestions", incidentId] })
    },
  })

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  const pendingSuggestions = suggestions?.filter((s: any) => s.status === "pending") || []

  if (!canManage || pendingSuggestions.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <GitMerge className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold">Possible Duplicates</h3>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => checkDuplicatesMutation.mutate()}
          disabled={checkingDuplicates}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${checkingDuplicates ? "animate-spin" : ""}`} />
          Check Again
        </Button>
      </div>

      {pendingSuggestions.map((suggestion: any) => {
        const similarity = Math.round(suggestion.similarity_score * 100)
        const isRecurrence = suggestion.match_reasons?.includes("possible_recurrence")
        
        return (
          <div
            key={suggestion.id}
            className={`border rounded-lg p-4 mb-3 ${
              isRecurrence 
                ? "border-amber-300 bg-amber-50" 
                : "border-blue-200 bg-blue-50"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {isRecurrence ? (
                    <AlertCircle className="h-5 w-5 text-amber-600" />
                  ) : (
                    <GitMerge className="h-5 w-5 text-blue-500" />
                  )}
                  <span className="font-medium">
                    {isRecurrence ? "Issue Happened Again" : "Similar Reports Found"}
                  </span>
                  <Badge variant={isRecurrence ? "destructive" : "default"}>
                    {similarity}% match
                  </Badge>
                </div>
                <p className="text-sm text-slate-600 ml-7">
                  {suggestion.duplicate_incident_ids.length} {suggestion.duplicate_incident_ids.length === 1 ? 'report' : 'reports'} might be the same issue
                </p>
              </div>
            </div>

            <div className="flex gap-2 ml-7">
              <Button
                size="sm"
                variant="default"
                onClick={() => approveMutation.mutate(suggestion.id)}
                disabled={approveMutation.isPending}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Merge Together
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => rejectMutation.mutate({ suggestionId: suggestion.id })}
                disabled={rejectMutation.isPending}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Keep Separate
              </Button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
