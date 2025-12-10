import React, { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { incidentsApi } from "../../api/incidents"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Skeleton } from "../ui/skeleton"
import { CheckCircle, AlertTriangle, GitMerge, RefreshCw, XCircle, Clock, Shield, Users } from "lucide-react"
import type { Incident } from "../../types/incident"

interface IncidentVerificationPanelProps {
  incidentId: string
  incident: Incident
  canManage: boolean
}

export const IncidentVerificationPanel: React.FC<IncidentVerificationPanelProps> = ({
  incidentId,
  incident,
  canManage,
}) => {
  const queryClient = useQueryClient()
  const [checkingDuplicates, setCheckingDuplicates] = useState(false)

  // Fetch merge suggestions
  const { data: suggestions, isLoading: suggestionsLoading } = useQuery({
    queryKey: ["merge-suggestions", incidentId],
    queryFn: () => incidentsApi.getMergeSuggestions(incidentId, "pending"),
    enabled: !!incidentId,
  })

  const checkDuplicatesMutation = useMutation({
    mutationFn: () => incidentsApi.checkDuplicates(incidentId),
    onMutate: () => setCheckingDuplicates(true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["merge-suggestions", incidentId] })
    },
    onSettled: () => setCheckingDuplicates(false),
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

  // AI Verification Status
  const verificationStatus = incident.ai_verification_status || 'pending'
  const confidenceScore = incident.ai_confidence_score
  const scorePercent = confidenceScore !== null && confidenceScore !== undefined 
    ? Math.round(confidenceScore * 100) 
    : null
  const isLowTrust = scorePercent !== null && scorePercent < 50

  // Merge Suggestions
  const pendingSuggestions = suggestions?.filter((s: any) => s.status === "pending") || []
  const hasDuplicates = pendingSuggestions.length > 0
  const hasVerification = verificationStatus !== 'pending'

  // Don't show if nothing to display
  if (!hasVerification && !hasDuplicates && !canManage) {
    return null
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold text-lg">Report Verification & Quality</h3>
        </div>
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

      {/* AI Verification Status */}
      {hasVerification && (
        <div className={`p-4 rounded-lg border ${
          verificationStatus === "verified"
            ? "bg-green-50 border-green-200"
            : verificationStatus === "to_be_verified"
            ? isLowTrust
              ? "bg-red-50 border-red-200"
              : "bg-amber-50 border-amber-200"
            : verificationStatus === "pending"
            ? "bg-blue-50 border-blue-200"
            : "bg-red-50 border-red-200"
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                {verificationStatus === "verified" && (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                )}
                {verificationStatus === "to_be_verified" && (
                  <AlertTriangle className={`h-5 w-5 ${isLowTrust ? "text-red-600" : "text-amber-600"}`} />
                )}
                {verificationStatus === "pending" && (
                  <Clock className="h-5 w-5 text-blue-600" />
                )}
                {verificationStatus === "failed" && (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
                <span className="font-semibold">
                  {verificationStatus === "verified" && "Report Verified"}
                  {verificationStatus === "to_be_verified" && (isLowTrust ? "Low Trust Score" : "Needs Review")}
                  {verificationStatus === "pending" && "Verification Pending"}
                  {verificationStatus === "failed" && "Verification Failed"}
                </span>
                {scorePercent !== null && (
                  <Badge variant={isLowTrust ? "destructive" : "default"}>
                    {scorePercent}% confidence
                  </Badge>
                )}
              </div>
              {incident.ai_verification_reason && (
                <p className="text-sm text-slate-600 mt-1">
                  {incident.ai_verification_reason}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Detection */}
      {suggestionsLoading ? (
        <Skeleton className="h-24 w-full" />
      ) : hasDuplicates ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-500" />
            <h4 className="font-semibold">Possible Duplicates</h4>
            <Badge>{pendingSuggestions.length} {pendingSuggestions.length === 1 ? 'match' : 'matches'}</Badge>
          </div>
          
          {pendingSuggestions.map((suggestion: any) => {
            const similarity = Math.round(suggestion.similarity_score * 100)
            const isRecurrence = suggestion.match_reasons?.includes("possible_recurrence")
            
            return (
              <div
                key={suggestion.id}
                className={`border rounded-lg p-4 ${
                  isRecurrence 
                    ? "border-amber-300 bg-amber-50" 
                    : "border-blue-200 bg-blue-50"
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {isRecurrence ? (
                        <AlertTriangle className="h-5 w-5 text-amber-600" />
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

                {canManage && (
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
                )}
              </div>
            )
          })}
        </div>
      ) : canManage ? (
        <div className="text-center py-4 text-slate-500 text-sm">
          No duplicate reports found. Click "Check for Duplicates" to search.
        </div>
      ) : null}
    </div>
  )
}
