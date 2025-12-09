import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "@tanstack/react-router";
import { format } from "date-fns";
import {
    AlertTriangle,
    ArrowLeft,
    CheckCircle,
    Clock,
    Image,
    Loader2,
    MapPin,
    User,
    Wrench,
    X,
} from "lucide-react";
import { incidentsApi } from "../../api/incidents";
import { usersApi } from "../../api/users";
import { IncidentActions } from "../../components/incidents/IncidentActions";
import { IncidentComments } from "../../components/incidents/IncidentComments";
import { IncidentMergeSuggestions } from "../../components/incidents/IncidentMergeSuggestions";
import { IncidentStatusBadge } from "../../components/incidents/IncidentStatusBadge";
import { IncidentWorkflowInfo } from "../../components/incidents/IncidentWorkflowInfo";
import { Button } from "../../components/ui/button";
import { Skeleton } from "../../components/ui/skeleton";
import { useAuthStore } from "../../stores/authStore";

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

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        <MapPin className="h-4 w-4" />
                        {incident.location?.geometry?.coordinates ? (
                            <a
                                href={`/map?lat=${
                                    incident.location.geometry.coordinates[1]
                                }&lng=${
                                    incident.location.geometry.coordinates[0]
                                }&zoom=18${
                                    incident.asset_id
                                        ? `&assetId=${incident.asset_id}`
                                        : ""
                                }`}
                                className="text-blue-600 hover:text-blue-800 hover:underline"
                                title="View on map"
                            >
                                {incident.location.geometry.coordinates[1]?.toFixed(
                                    6
                                )}
                                ,{" "}
                                {incident.location.geometry.coordinates[0]?.toFixed(
                                    6
                                )}
                            </a>
                        ) : (
                            <span>Location not specified</span>
                        )}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Clock className="h-4 w-4" />
                        <span>
                            Reported{" "}
                            {format(
                                new Date(incident.created_at),
                                "MMM d, yyyy HH:mm"
                            )}
                        </span>
                    </div>
                    {incident.assigned_to && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                            <User className="h-4 w-4" />
                            <span>Assigned to technician</span>
                        </div>
                    )}
                    {incident.resolved_at && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                            <CheckCircle className="h-4 w-4" />
                            <span>
                                Resolved{" "}
                                {format(
                                    new Date(incident.resolved_at),
                                    "MMM d, yyyy HH:mm"
                                )}
                            </span>
                        </div>
                    )}
                    {incident.reporter_type && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                            <User className="h-4 w-4" />
                            <span>Reported by: {incident.reporter_type}</span>
                        </div>
                    )}
                </div>

                {(user?.role === "admin" || user?.role === "technician") && (
                    <div className="bg-white rounded-lg border border-slate-200 p-6">
                        <IncidentMergeSuggestions
                            incidentId={id}
                            canManage={
                                user?.role === "admin" ||
                                user?.role === "technician"
                            }
                        />
                    </div>
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
                    {incident.status !== "resolved" &&
                        incident.status !== "closed" && (
                            <div className="mt-4 pt-4 border-t">
                                <Button
                                    variant="outline"
                                    onClick={() =>
                                        createMaintenanceMutation.mutate()
                                    }
                                    disabled={
                                        createMaintenanceMutation.isPending
                                    }
                                >
                                    <Wrench className="h-4 w-4 mr-2" />
                                    Create Maintenance Work Order
                                </Button>
                            </div>
                        )}
                    {/* AI Verification Status */}
                    {incident.ai_verification_status && (
                        <div
                            className={`mb-6 p-4 rounded-lg border ${
                                incident.ai_verification_status === "verified"
                                    ? "bg-green-50 border-green-200"
                                    : incident.ai_verification_status ===
                                      "to_be_verified"
                                    ? "bg-yellow-50 border-yellow-200"
                                    : incident.ai_verification_status ===
                                      "pending"
                                    ? "bg-blue-50 border-blue-200"
                                    : "bg-red-50 border-red-200"
                            }`}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                                        {incident.ai_verification_status ===
                                            "verified" && (
                                            <CheckCircle className="h-5 w-5 text-green-600" />
                                        )}
                                        {incident.ai_verification_status ===
                                            "to_be_verified" && (
                                            <AlertTriangle className="h-5 w-5 text-yellow-600" />
                                        )}
                                        {incident.ai_verification_status ===
                                            "pending" && (
                                            <Clock className="h-5 w-5 text-blue-600" />
                                        )}
                                        {incident.ai_verification_status ===
                                            "failed" && (
                                            <X className="h-5 w-5 text-red-600" />
                                        )}
                                        <span>AI Verification Status</span>
                                    </h3>
                                    <p className="text-sm mb-2">
                                        {incident.ai_verification_status ===
                                            "verified" &&
                                            "AI has verified this incident as legitimate."}
                                        {incident.ai_verification_status ===
                                            "to_be_verified" &&
                                            "This incident requires manual verification by an admin."}
                                        {incident.ai_verification_status ===
                                            "pending" &&
                                            "AI verification is in progress."}
                                        {incident.ai_verification_status ===
                                            "failed" &&
                                            "AI verification failed. Manual review required."}
                                    </p>
                                    {incident.ai_confidence_score !==
                                        undefined &&
                                        incident.ai_confidence_score !==
                                            null && (
                                            <p className="text-xs text-slate-600">
                                                Confidence Score:{" "}
                                                {(
                                                    incident.ai_confidence_score *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </p>
                                        )}
                                    {incident.ai_verification_reason && (
                                        <p className="text-xs text-slate-600 mt-1 italic">
                                            {incident.ai_verification_reason}
                                        </p>
                                    )}
                                </div>
                                {canVerify &&
                                    incident.ai_verification_status ===
                                        "to_be_verified" && (
                                        <Button
                                            size="sm"
                                            onClick={() =>
                                                verifyMutation.mutate()
                                            }
                                            disabled={verifyMutation.isPending}
                                            className="ml-4"
                                        >
                                            {verifyMutation.isPending ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <>
                                                    <CheckCircle className="h-4 w-4 mr-2" />
                                                    Verify
                                                </>
                                            )}
                                        </Button>
                                    )}
                            </div>
                        </div>
                    )}

                    <div className="mb-6">
                        <h2 className="font-semibold mb-2">Description</h2>
                        <p className="text-slate-700 whitespace-pre-wrap">
                            {incident.description}
                        </p>
                    </div>

                    {/* Photos Section */}
                    {incident.photos && incident.photos.length > 0 && (
                        <div className="mb-6">
                            <h2 className="font-semibold mb-3 flex items-center gap-2">
                                <Image className="h-4 w-4" />
                                Photos ({incident.photos.length})
                            </h2>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                {incident.photos.map((photo, index) => (
                                    <a
                                        key={index}
                                        href={photo}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block aspect-square rounded-lg overflow-hidden border border-slate-200 hover:border-blue-400 hover:shadow-md transition-all"
                                    >
                                        <img
                                            src={photo}
                                            alt={`Incident photo ${index + 1}`}
                                            className="w-full h-full object-cover"
                                        />
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Related Asset Section */}
                    {incident.asset_id && (
                        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <h2 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                                <Wrench className="h-4 w-4" />
                                Related Asset
                            </h2>
                            {incident.asset ? (
                                <div className="space-y-1">
                                    <p className="text-blue-800 font-medium">
                                        {incident.asset.name ||
                                            incident.asset.asset_code ||
                                            incident.asset.feature_type}
                                    </p>
                                    <div className="flex flex-wrap gap-2 text-sm text-blue-700">
                                        {incident.asset.asset_code && (
                                            <span className="bg-blue-100 px-2 py-0.5 rounded">
                                                Code:{" "}
                                                {incident.asset.asset_code}
                                            </span>
                                        )}
                                        {incident.asset.category && (
                                            <span className="bg-blue-100 px-2 py-0.5 rounded">
                                                {incident.asset.category}
                                            </span>
                                        )}
                                        {incident.asset.status && (
                                            <span className="bg-blue-100 px-2 py-0.5 rounded capitalize">
                                                {incident.asset.status}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <p className="text-blue-700 text-sm">
                                    Asset ID: {incident.asset_id}
                                </p>
                            )}
                            <Button
                                variant="outline"
                                size="sm"
                                className="mt-3"
                                onClick={() =>
                                    navigate({
                                        to: `/admin/assets/${incident.asset_id}`,
                                    })
                                }
                            >
                                View Asset Details
                            </Button>
                        </div>
                    )}

                    {/* Resolution Details */}
                    {incident.resolution_notes && (
                        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                            <h2 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                                <CheckCircle className="h-4 w-4" />
                                Resolution Details
                            </h2>
                            <div className="space-y-2">
                                <p className="text-green-800 whitespace-pre-wrap">
                                    {incident.resolution_notes}
                                </p>
                                {incident.resolution_type && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm text-green-700">
                                            Type:
                                        </span>
                                        <span className="text-sm font-medium text-green-800 capitalize">
                                            {incident.resolution_type}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="border-t pt-6">
                        <IncidentComments
                            comments={incident.comments}
                            onAddComment={async (comment, isInternal) => {
                                await commentMutation.mutateAsync({
                                    comment,
                                    isInternal,
                                });
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
