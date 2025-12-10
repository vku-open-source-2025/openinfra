import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { maintenanceApi } from "../../api/maintenance";
import { incidentsApi } from "../../api/incidents";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Label } from "../../components/ui/label";
import { Badge } from "../../components/ui/badge";
import {
    Loader2,
    ArrowLeft,
    MapPin,
    CheckCircle,
    Clock,
    PlayCircle,
    Camera,
    Wrench,
    Calendar,
    DollarSign,
    AlertCircle,
    XCircle,
    Image as ImageIcon,
    X,
    FileText,
} from "lucide-react";
import { format } from "date-fns";
import { useAuthStore } from "../../stores/authStore";

export const Route = createFileRoute("/technician/maintenance/$id")({
    component: MaintenanceDetailPage,
});

function MaintenanceDetailPage() {
    const { id } = Route.useParams();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const { user } = useAuthStore();

    const [completionNotes, setCompletionNotes] = useState("");
    const [actualCost, setActualCost] = useState<string>("");
    const [showCompleteForm, setShowCompleteForm] = useState(false);
    const [beforePhotos, setBeforePhotos] = useState<File[]>([]);
    const [afterPhotos, setAfterPhotos] = useState<File[]>([]);
    const [uploadingPhotos, setUploadingPhotos] = useState(false);
    const [photoType, setPhotoType] = useState<"before" | "after">("after");

    const { data: maintenance, isLoading } = useQuery({
        queryKey: ["maintenance", id],
        queryFn: () => maintenanceApi.getById(id),
    });

    // Find linked incident by searching for incidents with this maintenance_record_id
    const { data: incidents } = useQuery({
        queryKey: ["incidents", "maintenance", id],
        queryFn: async () => {
            const allIncidents = await incidentsApi.list({ limit: 1000 });
            return allIncidents.find(
                (inc) => inc.maintenance_record_id === id
            );
        },
        enabled: !!maintenance && (user?.role === "admin" || user?.role === "manager"),
    });

    const isAdmin = user?.role === "admin" || user?.role === "manager";
    const isTechnician = user?.role === "technician";

    const startMutation = useMutation({
        mutationFn: () => maintenanceApi.start(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["maintenance", id] });
            queryClient.invalidateQueries({
                queryKey: ["my-maintenance", user?.id],
            });
        },
    });

    const completeMutation = useMutation({
        mutationFn: (data: { notes: string; cost?: number }) =>
            maintenanceApi.complete(id, {
                work_performed: data.notes, // Required field
                actual_cost: data.cost,
                quality_checks: [],
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["maintenance", id] });
            queryClient.invalidateQueries({
                queryKey: ["my-maintenance", user?.id],
            });
            navigate({ to: "/technician" });
        },
    });

    const uploadPhotosMutation = useMutation({
        mutationFn: ({
            files,
            type,
        }: {
            files: File[];
            type: "before" | "after";
        }) => maintenanceApi.uploadPhotos(id, files, type),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["maintenance", id] });
            setBeforePhotos([]);
            setAfterPhotos([]);
            setUploadingPhotos(false);
        },
    });

    const handleStart = () => {
        startMutation.mutate();
    };

    const handleComplete = (e: React.FormEvent) => {
        e.preventDefault();
        if (!completionNotes.trim()) return;

        completeMutation.mutate({
            notes: completionNotes,
            cost: actualCost ? parseFloat(actualCost) : undefined,
        });
    };

    const handlePhotoUpload = async (type: "before" | "after") => {
        const photos = type === "before" ? beforePhotos : afterPhotos;
        if (photos.length === 0) return;

        setUploadingPhotos(true);
        try {
            await uploadPhotosMutation.mutateAsync({ files: photos, type });
        } catch (error) {
            console.error("Không thể tải ảnh:", error);
        } finally {
            setUploadingPhotos(false);
        }
    };

    const handleFileSelect = (
        e: React.ChangeEvent<HTMLInputElement>,
        type: "before" | "after"
    ) => {
        const files = Array.from(e.target.files || []);
        if (type === "before") {
            setBeforePhotos([...beforePhotos, ...files]);
        } else {
            setAfterPhotos([...afterPhotos, ...files]);
        }
    };

    const removePhoto = (index: number, type: "before" | "after") => {
        if (type === "before") {
            setBeforePhotos(beforePhotos.filter((_, i) => i !== index));
        } else {
            setAfterPhotos(afterPhotos.filter((_, i) => i !== index));
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
            </div>
        );
    }

    if (!maintenance) {
        return (
            <div className="p-8 text-center text-red-500">
                Không tìm thấy phiếu công việc bảo trì.
            </div>
        );
    }

    const getStatusConfig = () => {
        switch (maintenance.status) {
            case "scheduled":
                return {
                    icon: Calendar,
                    color: "text-blue-600",
                    bgColor: "bg-blue-50",
                    label: "Đã lên lịch",
                };
            case "in_progress":
                return {
                    icon: Wrench,
                    color: "text-orange-600",
                    bgColor: "bg-orange-50",
                    label: "Đang tiến hành",
                };
            case "completed":
                return {
                    icon: CheckCircle,
                    color: "text-green-600",
                    bgColor: "bg-green-50",
                    label: "Hoàn thành",
                };
            case "cancelled":
                return {
                    icon: XCircle,
                    color: "text-red-600",
                    bgColor: "bg-red-50",
                    label: "Đã hủy",
                };
            default:
                return {
                    icon: Clock,
                    color: "text-slate-600",
                    bgColor: "bg-slate-50",
                    label: maintenance.status,
                };
        }
    };

    const statusConfig = getStatusConfig();
    const StatusIcon = statusConfig.icon;

    const canStart = maintenance.status === "scheduled" && isTechnician;
    const canComplete = maintenance.status === "in_progress" && isTechnician;
    const canUploadPhotos =
        (maintenance.status === "in_progress" ||
            maintenance.status === "completed") && isTechnician;

    return (
        <div className="p-6 space-y-6">
            <Button
                variant="ghost"
                onClick={() =>
                    navigate({
                        to: isAdmin ? "/admin/incidents" : "/technician",
                    })
                }
            >
                <ArrowLeft className="mr-2 h-4 w-4" /> Quay lại công việc
            </Button>

            <div className="bg-white p-6 rounded-lg shadow-sm border space-y-6">
                {/* Header */}
                <div>
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                                <Badge
                                    variant="outline"
                                    className="font-mono text-xs"
                                >
                                    {maintenance.work_order_number}
                                </Badge>
                                <div
                                    className={`flex items-center gap-1 px-2 py-1 rounded-full text-sm font-medium ${statusConfig.bgColor} ${statusConfig.color}`}
                                >
                                    <StatusIcon className="h-4 w-4" />
                                    <span>{statusConfig.label}</span>
                                </div>
                                <Badge
                                    variant={
                                        maintenance.priority === "urgent" ||
                                        maintenance.priority === "high"
                                            ? "destructive"
                                            : maintenance.priority === "medium"
                                            ? "default"
                                            : "secondary"
                                    }
                                >
                                    {maintenance.priority}
                                </Badge>
                            </div>
                            <h1 className="text-2xl font-bold text-slate-900 mb-2">
                                {maintenance.title}
                            </h1>
                            <p className="text-slate-600">
                                {maintenance.description}
                            </p>
                        </div>
                    </div>

                    {/* Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-200">
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                            <Calendar className="h-4 w-4" />
                            <span>
                                <strong>Lên lịch:</strong>{" "}
                                {format(
                                    new Date(maintenance.scheduled_date),
                                    "MMM d, yyyy HH:mm"
                                )}
                            </span>
                        </div>
                        {maintenance.started_at && (
                            <div className="flex items-center gap-2 text-sm text-slate-600">
                                <Clock className="h-4 w-4" />
                                <span>
                                    <strong>Bắt đầu:</strong>{" "}
                                    {format(
                                        new Date(maintenance.started_at),
                                        "MMM d, yyyy HH:mm"
                                    )}
                                </span>
                            </div>
                        )}
                        {maintenance.completed_at && (
                            <div className="flex items-center gap-2 text-sm text-green-600">
                                <CheckCircle className="h-4 w-4" />
                                <span>
                                    <strong>Hoàn thành:</strong>{" "}
                                    {format(
                                        new Date(maintenance.completed_at),
                                        "MMM d, yyyy HH:mm"
                                    )}
                                </span>
                            </div>
                        )}
                        {maintenance.estimated_cost && (
                            <div className="flex items-center gap-2 text-sm text-slate-600">
                                <DollarSign className="h-4 w-4" />
                                <span>
                                    <strong>Chi phí ước tính:</strong> $
                                    {maintenance.estimated_cost.toFixed(2)}
                                </span>
                            </div>
                        )}
                        {maintenance.actual_cost && (
                            <div className="flex items-center gap-2 text-sm text-green-600">
                                <DollarSign className="h-4 w-4" />
                                <span>
                                    <strong>Chi phí thực tế:</strong> $
                                    {maintenance.actual_cost.toFixed(2)}
                                </span>
                            </div>
                        )}
                        {maintenance.asset_id && (
                            <div className="flex items-center gap-2 text-sm text-slate-600">
                                <MapPin className="h-4 w-4" />
                                <span>
                                    <strong>ID tài sản:</strong>{" "}
                                    {maintenance.asset_id}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Linked Incident Section - Show for admins */}
                {isAdmin && incidents && (
                    <div className="pt-4 border-t border-slate-200">
                        <h3 className="font-semibold mb-3 flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            Linked Incident Report
                        </h3>
                        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h4 className="font-semibold text-blue-900 mb-1">
                                        {incidents.title}
                                    </h4>
                                    <p className="text-sm text-blue-700 mb-2">
                                        {incidents.description}
                                    </p>
                                    <div className="flex flex-wrap gap-2 text-xs">
                                        <Badge variant="outline">
                                            {incidents.incident_number}
                                        </Badge>
                                        <Badge
                                            variant={
                                                incidents.severity === "critical" ||
                                                incidents.severity === "high"
                                                    ? "destructive"
                                                    : "default"
                                            }
                                        >
                                            {incidents.severity}
                                        </Badge>
                                        <Badge variant="secondary">
                                            {incidents.status}
                                        </Badge>
                                        {incidents.reported_at && (
                                            <span className="text-blue-600">
                                                Reported:{" "}
                                                {format(
                                                    new Date(
                                                        incidents.reported_at
                                                    ),
                                                    "MMM d, yyyy HH:mm"
                                                )}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() =>
                                        navigate({
                                            to: `/admin/incidents/${incidents.id}`,
                                        })
                                    }
                                >
                                    View Incident
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Notes Section */}
                {maintenance.notes && (
                    <div className="pt-4 border-t border-slate-200">
                        <h3 className="font-semibold mb-2">Ghi chú</h3>
                        <p className="text-sm text-slate-700 whitespace-pre-wrap">
                            {maintenance.notes}
                        </p>
                    </div>
                )}

                {/* Completion Notes */}
                {maintenance.status === "completed" && maintenance.notes && (
                    <div className="pt-4 border-t border-slate-200">
                        <h3 className="font-semibold mb-2">Ghi chú hoàn thành</h3>
                        <p className="text-sm text-slate-700 whitespace-pre-wrap">
                            {maintenance.notes}
                        </p>
                    </div>
                )}

                {/* Photos Section - Show for technicians (with upload) or admins (read-only) */}
                {(canUploadPhotos || (isAdmin && maintenance.attachments && maintenance.attachments.length > 0)) && (
                    <div className="pt-4 border-t border-slate-200">
                        <h3 className="font-semibold mb-4 flex items-center gap-2">
                            <Camera className="h-5 w-5" />
                            Ảnh
                        </h3>

                        {/* Before Photos */}
                        <div className="mb-6">
                            <Label className="mb-2 block">Ảnh trước</Label>
                            <div className="space-y-3">
                                <div className="flex gap-2">
                                    <Input
                                        type="file"
                                        accept="image/*"
                                        multiple
                                        onChange={(e) =>
                                            handleFileSelect(e, "before")
                                        }
                                        className="flex-1"
                                    />
                                    {beforePhotos.length > 0 && (
                                        <Button
                                            onClick={() =>
                                                handlePhotoUpload("before")
                                            }
                                            disabled={uploadingPhotos}
                                            size="sm"
                                        >
                                            {uploadingPhotos ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <>
                                                    <Camera className="h-4 w-4 mr-1" />
                                                    Tải lên
                                                </>
                                            )}
                                        </Button>
                                    )}
                                </div>
                                {beforePhotos.length > 0 && (
                                    <div className="flex flex-wrap gap-2">
                                        {beforePhotos.map((file, index) => (
                                            <div
                                                key={index}
                                                className="relative bg-slate-100 rounded p-2 flex items-center gap-2"
                                            >
                                                <ImageIcon className="h-4 w-4 text-slate-500" />
                                                <span className="text-xs text-slate-600 truncate max-w-[150px]">
                                                    {file.name}
                                                </span>
                                                <button
                                                    onClick={() =>
                                                        removePhoto(
                                                            index,
                                                            "before"
                                                        )
                                                    }
                                                    className="ml-auto text-red-500 hover:text-red-700"
                                                >
                                                    <X className="h-4 w-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* After Photos */}
                        <div className="mb-6">
                            <Label className="mb-2 block">Ảnh sau</Label>
                                    <div className="space-y-3">
                                        <div className="flex gap-2">
                                            <Input
                                                type="file"
                                                accept="image/*"
                                                multiple
                                                onChange={(e) =>
                                                    handleFileSelect(e, "before")
                                                }
                                                className="flex-1"
                                            />
                                            {beforePhotos.length > 0 && (
                                                <Button
                                                    onClick={() =>
                                                        handlePhotoUpload("before")
                                                    }
                                                    disabled={uploadingPhotos}
                                                    size="sm"
                                                >
                                                    {uploadingPhotos ? (
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                    ) : (
                                                        <>
                                                            <Camera className="h-4 w-4 mr-1" />
                                                            Tải lên
                                                        </>
                                                    )}
                                                </Button>
                                            )}
                                        </div>
                                        {beforePhotos.length > 0 && (
                                            <div className="flex flex-wrap gap-2">
                                                {beforePhotos.map((file, index) => (
                                                    <div
                                                        key={index}
                                                        className="relative bg-slate-100 rounded p-2 flex items-center gap-2"
                                                    >
                                                        <ImageIcon className="h-4 w-4 text-slate-500" />
                                                        <span className="text-xs text-slate-600 truncate max-w-[150px]">
                                                            {file.name}
                                                        </span>
                                                        <button
                                                            onClick={() =>
                                                                removePhoto(
                                                                    index,
                                                                    "before"
                                                                )
                                                            }
                                                            className="ml-auto text-red-500 hover:text-red-700"
                                                        >
                                                            <X className="h-4 w-4" />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* After Photos */}
                                <div className="mb-6">
                                    <Label className="mb-2 block">Ảnh sau</Label>
                                    <div className="space-y-3">
                                        <div className="flex gap-2">
                                            <Input
                                                type="file"
                                                accept="image/*"
                                                multiple
                                                onChange={(e) =>
                                                    handleFileSelect(e, "after")
                                                }
                                                className="flex-1"
                                            />
                                            {afterPhotos.length > 0 && (
                                                <Button
                                                    onClick={() =>
                                                        handlePhotoUpload("after")
                                                    }
                                                    disabled={uploadingPhotos}
                                                    size="sm"
                                                >
                                                    {uploadingPhotos ? (
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                    ) : (
                                                        <>
                                                            <Camera className="h-4 w-4 mr-1" />
                                                            Tải lên
                                                        </>
                                                    )}
                                                </Button>
                                            )}
                                        </div>
                                        {afterPhotos.length > 0 && (
                                            <div className="flex flex-wrap gap-2">
                                                {afterPhotos.map((file, index) => (
                                                    <div
                                                        key={index}
                                                        className="relative bg-slate-100 rounded p-2 flex items-center gap-2"
                                                    >
                                                        <ImageIcon className="h-4 w-4 text-slate-500" />
                                                        <span className="text-xs text-slate-600 truncate max-w-[150px]">
                                                            {file.name}
                                                        </span>
                                                        <button
                                                            onClick={() =>
                                                                removePhoto(
                                                                    index,
                                                                    "after"
                                                                )
                                                            }
                                                            className="ml-auto text-red-500 hover:text-red-700"
                                                        >
                                                            <X className="h-4 w-4" />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                        {/* Display existing photos - Show for both technicians and admins */}
                        {maintenance.attachments &&
                            maintenance.attachments.length > 0 && (
                                <div className={canUploadPhotos ? "mt-4 pt-4 border-t border-slate-200" : ""}>
                                    <h4 className="text-sm font-semibold mb-2">
                                        Ảnh đã tải lên
                                    </h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {maintenance.attachments.map(
                                            (attachment, index) => (
                                                <a
                                                    key={index}
                                                    href={attachment.file_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="block aspect-square rounded-lg overflow-hidden border border-slate-200 hover:border-blue-400 hover:shadow-md transition-all"
                                                >
                                                    <img
                                                        src={
                                                            attachment.file_url
                                                        }
                                                        alt={
                                                            attachment.file_name
                                                        }
                                                        className="w-full h-full object-cover"
                                                    />
                                                </a>
                                            )
                                        )}
                                    </div>
                                </div>
                            )}
                    </div>
                )}

                {/* Actions */}
                <div className="pt-4 border-t border-slate-200">
                    {canStart && (
                        <Button
                            className="w-full bg-blue-600 hover:bg-blue-700"
                            onClick={handleStart}
                            disabled={startMutation.isPending}
                        >
                            {startMutation.isPending ? (
                                <Loader2 className="animate-spin mr-2 h-4 w-4" />
                            ) : (
                                <PlayCircle className="mr-2 h-4 w-4" />
                            )}
                            Bắt đầu công việc
                        </Button>
                    )}

                    {canComplete && !showCompleteForm && (
                        <Button
                            className="w-full bg-green-600 hover:bg-green-700"
                            onClick={() => setShowCompleteForm(true)}
                        >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Hoàn thành công việc
                        </Button>
                    )}

                    {showCompleteForm && (
                        <form
                            onSubmit={handleComplete}
                            className="bg-slate-50 p-4 rounded border space-y-4"
                        >
                            <h3 className="font-semibold">
                                Chi tiết hoàn thành
                            </h3>
                            <div>
                                <Label htmlFor="work-performed">
                                    Công việc đã thực hiện *
                                </Label>
                                <Textarea
                                    id="work-performed"
                                    required
                                    value={completionNotes}
                                    onChange={(e) =>
                                        setCompletionNotes(e.target.value)
                                    }
                                    placeholder="Mô tả công việc đã thực hiện, bộ phận thay thế, vấn đề phát hiện..."
                                    rows={5}
                                />
                                <p className="text-xs text-slate-500 mt-1">
                                    Bắt buộc: Mô tả công việc đã thực hiện.
                                </p>
                            </div>
                            <div>
                                <Label htmlFor="actual-cost">
                                    Chi phí thực tế ($)
                                </Label>
                                <Input
                                    id="actual-cost"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={actualCost}
                                    onChange={(e) =>
                                        setActualCost(e.target.value)
                                    }
                                    placeholder="0.00"
                                />
                                <p className="text-xs text-slate-500 mt-1">
                                    Nhập chi phí thực tế nếu khác chi phí ước tính.
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="flex-1"
                                    onClick={() => {
                                        setShowCompleteForm(false);
                                        setCompletionNotes("");
                                        setActualCost("");
                                    }}
                                >
                                    Hủy
                                </Button>
                                <Button
                                    type="submit"
                                    className="flex-1 bg-green-600 hover:bg-green-700"
                                    disabled={
                                        completeMutation.isPending ||
                                        !completionNotes.trim()
                                    }
                                >
                                    {completeMutation.isPending && (
                                        <Loader2 className="animate-spin mr-2 h-4 w-4" />
                                    )}
                                    Gửi hoàn thành
                                </Button>
                            </div>
                        </form>
                    )}

                    {maintenance.status === "completed" &&
                        maintenance.approval_status === "pending" && (
                            <div className="bg-yellow-50 p-4 rounded border border-yellow-200 text-yellow-800 text-center">
                                <AlertCircle className="mx-auto h-8 w-8 mb-2 opacity-50" />
                                <p className="font-semibold">
                                    Đang chờ phê duyệt quản trị
                                </p>
                                <p className="text-sm">
                                    Công việc đã hoàn thành. Đang chờ phê duyệt chi phí.
                                </p>
                            </div>
                        )}

                    {maintenance.status === "completed" &&
                        maintenance.approval_status === "approved" && (
                            <div className="bg-green-50 p-4 rounded border border-green-200 text-green-800 text-center">
                                <CheckCircle className="mx-auto h-8 w-8 mb-2" />
                                <p className="font-semibold">
                                    Công việc đã hoàn thành và được phê duyệt
                                </p>
                            </div>
                        )}
                </div>
            </div>
        </div>
    );
}
