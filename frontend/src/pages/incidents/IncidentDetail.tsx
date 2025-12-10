import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useNavigate } from "@tanstack/react-router"
import { incidentsApi } from "../../api/incidents"
import { usersApi } from "../../api/users"
import { IncidentStatusBadge } from "../../components/incidents/IncidentStatusBadge"
import { IncidentComments } from "../../components/incidents/IncidentComments"
import { IncidentWorkflowInfo } from "../../components/incidents/IncidentWorkflowInfo"
import { IncidentHierarchy } from "../../components/incidents/IncidentHierarchy"
import { IncidentVerificationPanel } from "../../components/incidents/IncidentVerificationPanel"
import { Button } from "../../components/ui/button"
import { Skeleton } from "../../components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../../components/ui/dialog"
import { Select } from "../../components/ui/select"
import { ArrowLeft, MapPin, Clock, User, Wrench, CheckCircle, Loader2, Image, XCircle, GitMerge } from "lucide-react"
import { format } from "date-fns"
import { useAuthStore } from "../../stores/authStore"
import React, { useState } from "react"

const IncidentDetail: React.FC = () => {
    const { id } = useParams({ from: "/admin/incidents/$id" });
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const { user } = useAuthStore();
    const [showMaintenanceDialog, setShowMaintenanceDialog] = useState(false);
    const [showRejectDialog, setShowRejectDialog] = useState(false);
    const [selectedTechnician, setSelectedTechnician] = useState("");
    const [rejectReason, setRejectReason] = useState("");

    const { data: incident, isLoading } = useQuery({
        queryKey: ["incident", id],
        queryFn: () => incidentsApi.getById(id),
    });

    const { data: users, isLoading: isLoadingUsers, error: usersError } = useQuery({
        queryKey: ["technicians", "active"],
        queryFn: () => usersApi.listTechnicians("active"),
        enabled: showMaintenanceDialog, // Only fetch when dialog is open
        retry: 2,
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
        mutationFn: (technicianId?: string) => incidentsApi.createMaintenance(id, technicianId),
        onSuccess: (data) => {
            setShowMaintenanceDialog(false);
            setSelectedTechnician("");
            queryClient.invalidateQueries({ queryKey: ["incident", id] });
            queryClient.invalidateQueries({ queryKey: ["incidents"] });
            navigate({ to: `/technician/maintenance/${data.maintenance_id}` });
        },
        onError: (error: any) => {
            console.error("Failed to create maintenance:", error);
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

    // Fetch related incidents if this is a duplicate (must be before early returns)
    const { data: relatedIncidents } = useQuery({
        queryKey: ["related-incidents", id],
        queryFn: () => incidentsApi.getRelatedIncidents(id),
        enabled: !!id && !!incident?.related_incidents && incident.related_incidents.length > 0,
    });

    // Fetch merge suggestions to show duplicates (must be before early returns)
    const { data: mergeSuggestions } = useQuery({
        queryKey: ["merge-suggestions", id],
        queryFn: () => incidentsApi.getMergeSuggestions(id, "pending"),
        enabled: !!id,
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
                Không tìm thấy sự cố.
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

    return (
        <div className="p-6 space-y-6">
            <Button
                variant="ghost"
                onClick={() => navigate({ to: "/admin/incidents" })}
            >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Quay lại danh sách sự cố
            </Button>

            {/* Header Section */}
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
                                resolutionType={incident.resolution_type}
                                resolutionNotes={incident.resolution_notes}
                            />
                        </div>
                    </div>
                </div>

                {/* Location and Metadata */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        <MapPin className="h-4 w-4" />
                        {incident.location?.geometry?.coordinates ? (
                            (() => {
                                const coords = incident.location.geometry.coordinates;
                                // Handle GeoJSON Point format: [longitude, latitude]
                                if (Array.isArray(coords) && coords.length >= 2 && typeof coords[0] === 'number' && typeof coords[1] === 'number') {
                                    const lng = coords[0];
                                    const lat = coords[1];
                                    return (
                                        <a
                                            href={`/map?lat=${lat}&lng=${lng}&zoom=18${
                                                incident.asset_id
                                                    ? `&assetId=${incident.asset_id}`
                                                    : ""
                                            }`}
                                            className="text-blue-600 hover:text-blue-800 hover:underline"
                                            title="Xem trên bản đồ"
                                        >
                                            {lat.toFixed(6)}, {lng.toFixed(6)}
                                        </a>
                                    );
                                }
                                return <span>Chưa xác định vị trí</span>;
                            })()
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

                {/* Description */}
                <div className="mb-6">
                    <h2 className="font-semibold mb-2">Mô tả</h2>
                    <p className="text-slate-700 whitespace-pre-wrap">
                        {incident.description}
                    </p>
                </div>

                {/* Photos Section */}
                {incident.photos && incident.photos.length > 0 && (
                    <div className="mb-6">
                        <h2 className="font-semibold mb-3 flex items-center gap-2">
                            <Image className="h-4 w-4" />
                            Ảnh ({incident.photos.length})
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
                            Tài sản liên quan
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
                            Xem chi tiết tài sản
                        </Button>
                    </div>
                )}

                {/* Resolution Details */}
                {incident.resolution_notes && (
                    (() => {
                        // Check if this is a rejected incident
                        const resolutionNotesLower = incident.resolution_notes.toLowerCase();
                        const isRejected = resolutionNotesLower.includes('rejected') || 
                                          resolutionNotesLower.includes('từ chối') ||
                                          (incident.resolution_type === 'not_an_issue' || 
                                           incident.resolution_type === 'invalid');
                        
                        const bgColor = isRejected ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200';
                        const textColor = isRejected ? 'text-red-900' : 'text-green-900';
                        const textColorSecondary = isRejected ? 'text-red-800' : 'text-green-800';
                        const textColorTertiary = isRejected ? 'text-red-700' : 'text-green-700';
                        const Icon = isRejected ? XCircle : CheckCircle;

                        const getResolutionTypeLabel = (type?: string): string => {
                            if (!type) return '';
                            const typeMap: Record<string, string> = {
                                'fixed': 'Đã sửa chữa',
                                'duplicate': 'Trùng lặp',
                                'not_an_issue': 'Không phải sự cố',
                                'transferred': 'Đã chuyển giao',
                                'invalid': 'Không hợp lệ',
                                'deferred': 'Hoãn lại'
                            };
                            return typeMap[type] || type;
                        };

                        // Clean up the resolution notes - remove "Rejected:" prefix if present
                        const cleanNotes = incident.resolution_notes.replace(/^Rejected:\s*/i, '').trim();

                        return (
                            <div className={`mb-6 p-4 ${bgColor} border rounded-lg`}>
                                <h2 className={`font-semibold ${textColor} mb-2 flex items-center gap-2`}>
                                    <Icon className="h-4 w-4" />
                                    {isRejected ? 'Chi tiết từ chối' : 'Chi tiết xử lý'}
                                </h2>
                                <div className="space-y-2">
                                    <p className={`${textColorSecondary} whitespace-pre-wrap`}>
                                        {cleanNotes}
                                    </p>
                                    {incident.resolution_type && (
                                        <div className="flex items-center gap-2">
                                            <span className={`text-sm ${textColorTertiary}`}>
                                                Loại:
                                            </span>
                                            <span className={`text-sm font-medium ${textColorSecondary}`}>
                                                {getResolutionTypeLabel(incident.resolution_type)}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })()
                )}
            </div>

            {/* Related Reports - Show main report with sub-reports */}
            <IncidentHierarchy incidentId={id} incident={incident} />

            {/* Duplicate/Related Incidents Section */}
            {(incident.resolution_type === "duplicate" || 
              (relatedIncidents && relatedIncidents.length > 0) ||
              (mergeSuggestions && mergeSuggestions.length > 0)) && (
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <h2 className="font-semibold mb-4 flex items-center gap-2">
                        <GitMerge className="h-5 w-5 text-blue-500" />
                        Related/Duplicate Reports
                    </h2>
                    <div className="space-y-3">
                        {incident.resolution_type === "duplicate" && (
                            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                <p className="text-sm text-blue-800">
                                    <strong>This incident has been marked as a duplicate.</strong>
                                    {incident.resolution_notes && (
                                        <span className="ml-2">{incident.resolution_notes}</span>
                                    )}
                                </p>
                            </div>
                        )}
                        
                        {relatedIncidents && relatedIncidents.length > 0 && (
                            <div>
                                <h3 className="text-sm font-medium text-slate-700 mb-2">
                                    Merged/Related Incidents ({relatedIncidents.length}):
                                </h3>
                                <div className="space-y-2">
                                    {relatedIncidents.map((related) => (
                                        <div
                                            key={related.id}
                                            className="p-3 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer"
                                            onClick={() => navigate({ to: `/admin/incidents/${related.id}` })}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <p className="font-medium text-slate-900">
                                                        {related.title}
                                                    </p>
                                                    <p className="text-sm text-slate-600">
                                                        {related.incident_number || `#${related.id.slice(-8)}`} • 
                                                        {format(new Date(related.created_at), "MMM d, yyyy HH:mm")}
                                                    </p>
                                                </div>
                                                <IncidentStatusBadge
                                                    status={related.status}
                                                    severity={related.severity}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {mergeSuggestions && mergeSuggestions.length > 0 && (
                            <div>
                                <h3 className="text-sm font-medium text-slate-700 mb-2">
                                    Possible Duplicates ({mergeSuggestions.length}):
                                </h3>
                                <div className="space-y-2">
                                    {mergeSuggestions.map((suggestion: any) => {
                                        const similarity = Math.round(suggestion.similarity_score * 100)
                                        const matchReasons = suggestion.match_reasons || []
                                        
                                        const reasonLabels: Record<string, string> = {
                                            "same_asset": "Same asset",
                                            "very_similar_description": "Very similar description",
                                            "similar_description": "Similar description",
                                            "similar_images": "Similar images",
                                            "nearby_location": "Nearby location",
                                            "possible_recurrence": "Possible recurrence",
                                            "reported_during_work": "Reported during work"
                                        }
                                        
                                        const translatedReasons = matchReasons
                                            .map((r: string) => reasonLabels[r] || r)
                                            .filter(Boolean)
                                        
                                        return (
                                            <div
                                                key={suggestion.id}
                                                className="p-3 border border-amber-200 bg-amber-50 rounded-lg"
                                            >
                                                <p className="text-sm text-amber-800 mb-2">
                                                    <strong>Similarity: {similarity}%</strong>
                                                    {translatedReasons.length > 0 && (
                                                        <span className="ml-2 text-xs">
                                                            ({translatedReasons.join(", ")})
                                                        </span>
                                                    )}
                                                </p>
                                                <div className="space-y-1">
                                                    {suggestion.duplicate_incident_ids.map((dupId: string) => (
                                                        <button
                                                            key={dupId}
                                                            onClick={() => navigate({ to: `/admin/incidents/${dupId}` })}
                                                            className="text-sm text-blue-600 hover:text-blue-800 hover:underline block"
                                                        >
                                                            View Incident #{dupId.slice(-8)}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Unified Verification & Duplicate Detection Panel */}
            {(user?.role === "admin" || user?.role === "technician") && (
                <IncidentVerificationPanel
                    incidentId={id}
                    incident={incident}
                    canManage={user?.role === "admin" || user?.role === "technician"}
                />
            )}

            {/* Actions Section */}
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="font-semibold mb-4">Hành động</h2>
                <div className="space-y-3">
                    {/* Create Maintenance Button */}
                    {incident.status !== "closed" && !incident.maintenance_record_id && (
                        <Button
                            onClick={() => setShowMaintenanceDialog(true)}
                            disabled={createMaintenanceMutation.isPending || !incident.asset_id}
                            className="w-full"
                            title={!incident.asset_id ? "Sự cố phải được liên kết với tài sản để tạo phiếu bảo trì" : undefined}
                        >
                            {createMaintenanceMutation.isPending ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Đang tạo...
                                </>
                            ) : (
                                <>
                                    <Wrench className="h-4 w-4 mr-2" />
                                    Tạo phiếu bảo trì
                                </>
                            )}
                        </Button>
                    )}

                    {/* Reject Button - Hide when maintenance ticket exists */}
                    {canReject && !incident.maintenance_record_id && (
                        <Button
                            variant="outline"
                            onClick={() => setShowRejectDialog(true)}
                            disabled={rejectMutation.isPending}
                            className="w-full text-red-600 border-red-200 hover:bg-red-50"
                        >
                            {rejectMutation.isPending ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Đang xử lý...
                                </>
                            ) : (
                                <>
                                    <XCircle className="h-4 w-4 mr-2" />
                                    Từ chối
                                </>
                            )}
                        </Button>
                    )}
                </div>

                {/* Create Maintenance Dialog */}
                <Dialog open={showMaintenanceDialog} onOpenChange={setShowMaintenanceDialog}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Tạo phiếu bảo trì</DialogTitle>
                            <DialogDescription>
                                Chọn kỹ thuật viên để thực hiện công việc bảo trì này.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            {/* Error message */}
                            {createMaintenanceMutation.isError && (
                                <div className="text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
                                    <p className="font-medium">Không thể tạo phiếu bảo trì</p>
                                    <p className="text-xs mt-1">
                                        {createMaintenanceMutation.error?.response?.data?.detail || 
                                         (createMaintenanceMutation.error as any)?.message || 
                                         "Vui lòng thử lại sau."}
                                    </p>
                                </div>
                            )}
                            
                            {/* Warning if incident has no asset */}
                            {!incident.asset_id && (
                                <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded border border-amber-200">
                                    <p className="font-medium">Cảnh báo</p>
                                    <p className="text-xs mt-1">
                                        Sự cố này chưa được liên kết với tài sản. Bạn cần liên kết sự cố với một tài sản trước khi tạo phiếu bảo trì.
                                    </p>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Kỹ thuật viên
                                </label>
                                {isLoadingUsers ? (
                                    <div className="flex items-center gap-2 text-sm text-slate-500">
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        <span>Đang tải danh sách kỹ thuật viên...</span>
                                    </div>
                                ) : usersError ? (
                                    <div className="text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
                                        <p className="font-medium">Lỗi khi tải danh sách kỹ thuật viên.</p>
                                        <p className="text-xs mt-1">
                                            {usersError instanceof Error ? usersError.message : "Vui lòng thử lại."}
                                        </p>
                                    </div>
                                ) : (
                                    <Select
                                        value={selectedTechnician}
                                        onChange={(e) => setSelectedTechnician(e.target.value)}
                                        placeholder="Chọn kỹ thuật viên..."
                                        disabled={!incident.asset_id}
                                    >
                                        {users && users.length > 0 ? (
                                            users.map((user) => (
                                                <option key={user.id} value={user.id}>
                                                    {user.full_name || user.username}
                                                </option>
                                            ))
                                        ) : (
                                            <option value="" disabled>
                                                Không có kỹ thuật viên nào
                                            </option>
                                        )}
                                    </Select>
                                )}
                            </div>
                            <div className="flex gap-2 justify-end">
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        setShowMaintenanceDialog(false);
                                        setSelectedTechnician("");
                                    }}
                                >
                                    Hủy
                                </Button>
                                <Button
                                    onClick={() => {
                                        createMaintenanceMutation.mutate(
                                            selectedTechnician || undefined
                                        );
                                    }}
                                    disabled={createMaintenanceMutation.isPending || !incident.asset_id}
                                >
                                    {createMaintenanceMutation.isPending ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Đang tạo...
                                        </>
                                    ) : (
                                        "Tạo phiếu bảo trì"
                                    )}
                                </Button>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>

                {/* Reject Dialog */}
                <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Từ chối sự cố</DialogTitle>
                            <DialogDescription>
                                Vui lòng nhập lý do từ chối sự cố này.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Lý do từ chối
                                </label>
                                <textarea
                                    value={rejectReason}
                                    onChange={(e) => setRejectReason(e.target.value)}
                                    placeholder="Nhập lý do từ chối..."
                                    rows={4}
                                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                                />
                            </div>
                            <div className="flex gap-2 justify-end">
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        setShowRejectDialog(false);
                                        setRejectReason("");
                                    }}
                                >
                                    Hủy
                                </Button>
                                <Button
                                    onClick={async () => {
                                        if (rejectReason.trim()) {
                                            await rejectMutation.mutateAsync(rejectReason);
                                            setShowRejectDialog(false);
                                            setRejectReason("");
                                        }
                                    }}
                                    disabled={!rejectReason.trim() || rejectMutation.isPending}
                                    className="bg-red-600 hover:bg-red-700"
                                >
                                    {rejectMutation.isPending ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Đang xử lý...
                                        </>
                                    ) : (
                                        "Xác nhận từ chối"
                                    )}
                                </Button>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>
                    {/* Show linked maintenance record if exists */}
                    {incident.maintenance_record_id && (
                        <div className="mt-4 pt-4">
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
                                                to: `/technician/maintenance/${incident.maintenance_record_id}`,
                                            })
                                        }
                                    >
                                        Xem bảo trì
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}

                {/* Phần bình luận */}
                <div className="pt-6 mt-6">
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
        </div>
    );
};

export default IncidentDetail;
