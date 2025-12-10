import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useNavigate } from "@tanstack/react-router"
import { incidentsApi } from "../../api/incidents"
import { usersApi } from "../../api/users"
import { IncidentStatusBadge } from "../../components/incidents/IncidentStatusBadge"
import { IncidentComments } from "../../components/incidents/IncidentComments"
import { IncidentActions } from "../../components/incidents/IncidentActions"
import { IncidentWorkflowInfo } from "../../components/incidents/IncidentWorkflowInfo"
import { IncidentMergeSuggestions } from "../../components/incidents/IncidentMergeSuggestions"
import { IncidentHierarchy } from "../../components/incidents/IncidentHierarchy"
import { Button } from "../../components/ui/button"
import { Skeleton } from "../../components/ui/skeleton"
import { ArrowLeft, MapPin, Clock, User, Wrench, CheckCircle, Loader2, Image, X, AlertTriangle } from "lucide-react"
import { format } from "date-fns"
import { useAuthStore } from "../../stores/authStore"

const IncidentDetail: React.FC = () => {
    const { id } = useParams({ from: "/admin/incidents/$id" });
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const { user } = useAuthStore();

    const { data: incident, isLoading } = useQuery({
        queryKey: ["incident", id],
        queryFn: () => incidentsApi.getById(id),
    });

    const { data: users } = useQuery({
        queryKey: ["users"],
        queryFn: () => usersApi.list({ role: "technician", status: "active" }),
        enabled: user?.role === "admin" || user?.role === "manager",
    });

    const acknowledgeMutation = useMutation({
        mutationFn: () => incidentsApi.acknowledge(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
        },
    });

    const assignMutation = useMutation({
        mutationFn: (userId: string) => incidentsApi.assign(id, userId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
        },
    });

    const resolveMutation = useMutation({
        mutationFn: ({
            notes,
            type,
        }: {
            notes: string;
            type: "fixed" | "duplicate" | "invalid" | "deferred";
        }) => incidentsApi.resolve(id, notes, type),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
        },
    });

    const commentMutation = useMutation({
        mutationFn: ({
            comment,
            isInternal,
        }: {
            comment: string;
            isInternal: boolean;
        }) => incidentsApi.addComment(id, { comment, is_internal: isInternal }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
        },
    });
    const createMaintenanceMutation = useMutation({
        mutationFn: () => incidentsApi.createMaintenance(id),
        onSuccess: (data) => {
            navigate({ to: `/admin/maintenance/${data.maintenance_id}` });
        },
    });

    const approveCostMutation = useMutation({
        mutationFn: () => incidentsApi.approveCost(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
        },
    });

    const closeMutation = useMutation({
        mutationFn: (notes?: string) => incidentsApi.close(id, notes),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
        },
    });

    const rejectMutation = useMutation({
        mutationFn: (reason: string) => incidentsApi.reject(id, reason),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
        },
    });

    const verifyMutation = useMutation({
        mutationFn: () => incidentsApi.verify(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
        },
    });

    if (isLoading) {
        return (
            <div className="p-6 space-y-4">
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    if (!incident) {
        return (
            <div className="p-6 text-center text-red-500">
                Incident not found.
            </div>
        );
    }

    // Permission checks based on API documentation workflow
    const canAcknowledge =
        (user?.role === "admin" || user?.role === "manager") &&
        incident.status === "reported";
    const canAssign =
        (user?.role === "admin" || user?.role === "manager") &&
        incident.status === "acknowledged";
    const canResolve =
        (user?.role === "admin" ||
            user?.role === "manager" ||
            user?.role === "technician") &&
        incident.status === "investigating";
    const canAddInternal =
        user?.role === "admin" ||
        user?.role === "manager" ||
        user?.role === "technician";
    const canClose =
        (user?.role === "admin" || user?.role === "manager") &&
        incident.status === "resolved";
    const canReject =
        (user?.role === "admin" || user?.role === "manager") &&
        (incident.status === "reported" || incident.status === "acknowledged");
    const canVerify =
        (user?.role === "admin" || user?.role === "manager") &&
        (incident.ai_verification_status === "to_be_verified" ||
            incident.ai_verification_status === "pending");
    const canApproveCost =
        (user?.role === "admin" || user?.role === "manager") &&
        (incident.status === "resolved" ||
            incident.status === "waiting_approval");

    return (
        <div className="p-6 space-y-6">
            <Button
                variant="ghost"
                onClick={() => navigate({ to: "/admin/incidents" })}
            >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Incidents
            </Button>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                        <h1 className="text-2xl font-bold text-slate-900 mb-2">
                            {incident.title}
                        </h1>
                        <div className="flex items-center gap-3">
                            <IncidentStatusBadge
                                status={incident.status}
                                severity={incident.severity}
                            />
                            <IncidentWorkflowInfo
                                currentStatus={incident.status}
                            />
                        </div>
                    </div>
                </div>

      {/* Related Reports - Show main report with sub-reports */}
      <IncidentHierarchy incidentId={id} incident={incident} />

      {/* Merge Suggestions - Only show if admin/technician */}
      {(user?.role === "admin" || user?.role === "technician") && (
        <IncidentMergeSuggestions
          incidentId={id}
          canManage={user?.role === "admin" || user?.role === "technician"}
        />
      )}

                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <h2 className="font-semibold mb-4">Actions</h2>
                    <IncidentActions
                        incident={incident}
                        onAcknowledge={async () => {
                            await acknowledgeMutation.mutateAsync();
                        }}
                        onAssign={async (userId) => {
                            await assignMutation.mutateAsync(userId);
                        }}
                        onResolve={async (notes, type) => {
                            await resolveMutation.mutateAsync({ notes, type });
                        }}
                        onClose={async (notes) => {
                            await closeMutation.mutateAsync(notes);
                        }}
                        onReject={async (reason) => {
                            await rejectMutation.mutateAsync(reason);
                        }}
                        onVerify={async () => {
                            await verifyMutation.mutateAsync();
                        }}
                        availableUsers={users || []}
                        canAcknowledge={canAcknowledge}
                        canAssign={canAssign}
                        canResolve={canResolve}
                        canClose={canClose}
                        canReject={canReject}
                        canVerify={canVerify}
                    />
                    {/* Create Maintenance - available when incident is investigating or resolved, and not already linked */}
                    {incident.status !== "closed" &&
                        !incident.maintenance_record_id && (
                            <div className="mt-4 pt-4 border-t">
                                <div className="mb-2">
                                    <p className="text-sm text-slate-600 mb-2">
                                        Create a maintenance work order linked
                                        to this incident.
                                        {incident.asset_id &&
                                            " This will automatically link to the related asset."}
                                    </p>
                                </div>
                                <Button
                                    variant="outline"
                                    onClick={() =>
                                        createMaintenanceMutation.mutate()
                                    }
                                    disabled={
                                        createMaintenanceMutation.isPending
                                    }
                                >
                                    {createMaintenanceMutation.isPending ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Creating...
                                        </>
                                    ) : (
                                        <>
                                            <Wrench className="h-4 w-4 mr-2" />
                                            Create Maintenance Work Order
                                        </>
                                    )}
                                </Button>
                            </div>
                        )}
                    {/* Show linked maintenance record if exists */}
                    {incident.maintenance_record_id && (
                        <div className="mt-4 pt-4 border-t">
                            <div className="bg-green-50 border border-green-200 p-4 rounded">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-semibold text-green-800 mb-1">
                                            Maintenance Work Order
                                        </h3>
                                        <p className="text-sm text-green-700">
                                            Linked maintenance record:{" "}
                                            {incident.maintenance_record_id}
                                        </p>
                                    </div>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() =>
                                            navigate({
                                                to: `/admin/maintenance/${incident.maintenance_record_id}`,
                                            })
                                        }
                                    >
                                        View Maintenance
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Approve Cost - shown when incident is resolved and has maintenance record */}
                    {canApproveCost && incident.maintenance_record_id && (
                        <div className="mt-4 pt-4 border-t">
                            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded mb-4">
                                <h3 className="font-semibold text-yellow-800">
                                    Cost Approval Required
                                </h3>
                                <p className="text-sm text-yellow-700">
                                    This incident has pending maintenance costs
                                    that require approval. Approving will
                                    automatically resolve the incident.
                                </p>
                            </div>
                            <Button
                                className="w-full sm:w-auto bg-green-600 hover:bg-green-700"
                                onClick={() => approveCostMutation.mutate()}
                                disabled={approveCostMutation.isPending}
                            >
                                {approveCostMutation.isPending ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                    <CheckCircle className="mr-2 h-4 w-4" />
                                )}
                                Approve Cost & Resolve
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default IncidentDetail;
