import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useNavigate } from "@tanstack/react-router"
import { incidentsApi } from "../../api/incidents"
import { usersApi } from "../../api/users"
import { IncidentStatusBadge } from "../../components/incidents/IncidentStatusBadge"
import { IncidentComments } from "../../components/incidents/IncidentComments"
import { IncidentActions } from "../../components/incidents/IncidentActions"
import { Button } from "../../components/ui/button"
import { Skeleton } from "../../components/ui/skeleton"
import { ArrowLeft, MapPin, Clock, User, Wrench, CheckCircle, Loader2 } from "lucide-react"
import { format } from "date-fns"
import { useAuthStore } from "../../stores/authStore"

const IncidentDetail: React.FC = () => {
  const { id } = useParams({ from: "/admin/incidents/$id" })
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()

  const { data: incident, isLoading } = useQuery({
    queryKey: ["incident", id],
    queryFn: () => incidentsApi.getById(id),
  })

  const { data: users } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list({ role: "technician", status: "active" }),
    enabled: user?.role === "admin" || user?.role === "manager",
  })

  const acknowledgeMutation = useMutation({
    mutationFn: () => incidentsApi.acknowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", id] })
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
    },
  })

  const assignMutation = useMutation({
    mutationFn: (userId: string) => incidentsApi.assign(id, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", id] })
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
    },
  })

  const resolveMutation = useMutation({
    mutationFn: ({ notes, type }: { notes: string; type: "fixed" | "duplicate" | "invalid" | "deferred" }) =>
      incidentsApi.resolve(id, notes, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", id] })
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
    },
  })

  const commentMutation = useMutation({
    mutationFn: ({ comment, isInternal }: { comment: string; isInternal: boolean }) =>
      incidentsApi.addComment(id, { comment, is_internal: isInternal }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", id] })
    },
  })
  const createMaintenanceMutation = useMutation({
    mutationFn: () => incidentsApi.createMaintenance(id),
    onSuccess: (data) => {
      navigate({ to: `/admin/maintenance/${data.maintenance_id}` })
    },
  })

  const approveCostMutation = useMutation({
    mutationFn: () => incidentsApi.approveCost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", id] })
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
    }
  })


  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="p-6 text-center text-red-500">
        Incident not found.
      </div>
    )
  }

  const canAcknowledge = (user?.role === "admin" || user?.role === "manager") && incident.status === "reported"
  const canAssign = (user?.role === "admin" || user?.role === "manager") && incident.status === "acknowledged"
  const canResolve = (user?.role === "admin" || user?.role === "manager" || user?.role === "technician") &&
    (incident.status === "assigned" || incident.status === "in_progress")
  const canAddInternal = user?.role === "admin" || user?.role === "manager" || user?.role === "technician"

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/incidents" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Incidents
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-slate-900 mb-2">{incident.title}</h1>
            <IncidentStatusBadge status={incident.status} severity={incident.severity} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <MapPin className="h-4 w-4" />
            <span>{incident.location?.address || "Location not specified"}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Clock className="h-4 w-4" />
            <span>Reported {format(new Date(incident.created_at), "MMM d, yyyy HH:mm")}</span>
          </div>
          {incident.assigned_to && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <User className="h-4 w-4" />
              <span>Assigned to technician</span>
            </div>
          )}
        </div>

        <div className="mb-6">
          <h2 className="font-semibold mb-2">Description</h2>
          <p className="text-slate-700 whitespace-pre-wrap">{incident.description}</p>
        </div>

        {incident.asset_id && (
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => navigate({ to: `/admin/assets/${incident.asset_id}` })}
            >
              View Related Asset
            </Button>
          </div>
        )}

        <div className="border-t pt-6">
          <IncidentComments
            comments={incident.comments}
            onAddComment={async (comment, isInternal) => {
              await commentMutation.mutateAsync({ comment, isInternal })
            }}
            canAddInternal={canAddInternal}
          />
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h2 className="font-semibold mb-4">Actions</h2>
        <IncidentActions
          incident={incident}
          onAcknowledge={async () => {
            await acknowledgeMutation.mutateAsync()
          }}
          onAssign={async (userId) => {
            await assignMutation.mutateAsync(userId)
          }}
          onResolve={async (notes, type) => {
            await resolveMutation.mutateAsync({ notes, type })
          }}
          availableUsers={users || []}
          canAcknowledge={canAcknowledge}
          canAssign={canAssign}
          canResolve={canResolve}
        />
        {incident.status !== "resolved" && incident.status !== "closed" && (
          <div className="mt-4 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => createMaintenanceMutation.mutate()}
              disabled={createMaintenanceMutation.isPending}
            >
              <Wrench className="h-4 w-4 mr-2" />
              Create Maintenance Work Order
            </Button>
          </div>
        )}

        {incident.status === 'waiting_approval' && (user?.role === 'admin' || user?.role === 'manager') && (
          <div className="mt-4 pt-4 border-t">
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded mb-4">
              <h3 className="font-semibold text-yellow-800">Cost Approval Required</h3>
              <p className="text-sm text-yellow-700">This incident has pending maintenance costs that require approval.</p>
            </div>
            <Button
              className="w-full sm:w-auto bg-green-600 hover:bg-green-700"
              onClick={() => approveCostMutation.mutate()}
              disabled={approveCostMutation.isPending}
            >
              {approveCostMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle className="mr-2 h-4 w-4" />}
              Approve Cost & Resolve
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

export default IncidentDetail
