import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { incidentsApi } from "../../api/incidents";
import { maintenanceApi } from "../../api/maintenance";
import type { Incident } from "../../types/incident";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Label } from "../../components/ui/label";
import {
    Loader2,
    ArrowLeft,
    MapPin,
    CheckCircle,
    Clock,
    PlayCircle,
    Wrench,
    ExternalLink,
} from "lucide-react";

export const Route = createFileRoute("/technician/tasks/$taskId")({
    component: TaskExecutionPage,
});

function TaskExecutionPage() {
    const { taskId } = Route.useParams();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [cost, setCost] = useState<string>("");
    const [notes, setNotes] = useState("");
    const [resolutionType, setResolutionType] = useState<
        "fixed" | "duplicate" | "invalid" | "deferred"
    >("fixed");
    const [showCompleteForm, setShowCompleteForm] = useState(false);
    const [showResolveForm, setShowResolveForm] = useState(false);

    const { data: incident, isLoading } = useQuery({
        queryKey: ["incident", taskId],
        queryFn: () => incidentsApi.getById(taskId),
    });

    const { data: maintenance, isLoading: loadingMaint } = useQuery({
        queryKey: ["maintenance", incident?.maintenance_record_id],
        queryFn: () => maintenanceApi.getById(incident!.maintenance_record_id!),
        enabled: !!incident?.maintenance_record_id,
    });

    const startMutation = useMutation({
        mutationFn: (maintId: string) => maintenanceApi.start(maintId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", taskId] });
            queryClient.invalidateQueries({ queryKey: ["maintenance"] });
        },
    });

    const resolveIncidentMutation = useMutation({
        mutationFn: ({
            notes,
            type,
        }: {
            notes: string;
            type: "fixed" | "duplicate" | "invalid" | "deferred";
        }) => incidentsApi.resolve(taskId, notes, type),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", taskId] });
            queryClient.invalidateQueries({
                queryKey: ["my-incidents", user?.id],
            });
            navigate({ to: "/technician" });
        },
    });

    const completeMutation = useMutation({
        mutationFn: (data: { id: string; notes: string; cost: number }) =>
            maintenanceApi.complete(data.id, {
                work_performed: data.notes, // Required field
                actual_cost: data.cost,
                quality_checks: [],
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["incident", taskId] });
            queryClient.invalidateQueries({ queryKey: ["maintenance"] });
            navigate({ to: "/technician" });
        },
    });

    if (isLoading || loadingMaint)
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="animate-spin" />
            </div>
        );
    if (!incident) return <div className="p-8 text-center">Task not found</div>;

    const handleStart = () => {
        if (incident.maintenance_record_id) {
            startMutation.mutate(incident.maintenance_record_id);
        }
    };

    const handleComplete = (e: React.FormEvent) => {
        e.preventDefault();
        if (incident.maintenance_record_id) {
            completeMutation.mutate({
                id: incident.maintenance_record_id,
                notes,
                cost: parseFloat(cost) || 0,
            });
        }
    };

    const handleResolveIncident = (e: React.FormEvent) => {
        e.preventDefault();
        if (!notes.trim()) return;
        resolveIncidentMutation.mutate({ notes, type: resolutionType });
    };

    return (
        <div className="space-y-6">
            <Button
                variant="ghost"
                className="pl-0"
                onClick={() => navigate({ to: "/technician" })}
            >
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to Tasks
            </Button>

            <div className="bg-white p-4 rounded-lg shadow-sm border space-y-4">
                <div>
                    <span
                        className={`inline-block px-2 py-1 rounded-full text-xs font-semibold mb-2
                   ${
                       incident.severity === "critical"
                           ? "bg-red-100 text-red-800"
                           : "bg-blue-100 text-blue-800"
                   }`}
                    >
                        {incident.severity.toUpperCase()}
                    </span>
                    <h1 className="text-xl font-bold">{incident.title}</h1>
                    <p className="text-slate-600 mt-1">
                        {incident.description}
                    </p>
                </div>

                <div className="flex items-center text-sm text-slate-500">
                    <MapPin className="mr-2 h-4 w-4" />
                    {incident.location?.address}
                </div>

                {/* Maintenance Work Order Link */}
                {incident.maintenance_record_id && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Wrench className="h-5 w-5 text-blue-600" />
                                <div>
                                    <p className="font-semibold text-blue-900">
                                        Maintenance Work Order
                                    </p>
                                    <p className="text-sm text-blue-700">
                                        Linked maintenance record available
                                    </p>
                                </div>
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
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View Maintenance
                            </Button>
                        </div>
                    </div>
                )}

                {/* Actions based on Status */}
                {incident.status === "investigating" && (
                    <>
                        {incident.maintenance_record_id &&
                            maintenance &&
                            maintenance.status === "scheduled" && (
                                <Button
                                    className="w-full bg-blue-600"
                                    onClick={handleStart}
                                    disabled={startMutation.isPending}
                                >
                                    {startMutation.isPending ? (
                                        <Loader2 className="animate-spin mr-2" />
                                    ) : (
                                        <PlayCircle className="mr-2" />
                                    )}
                                    Start Maintenance Work
                                </Button>
                            )}

                        {maintenance &&
                            maintenance.status === "in_progress" &&
                            !showCompleteForm && (
                                <Button
                                    className="w-full bg-green-600"
                                    onClick={() => setShowCompleteForm(true)}
                                >
                                    <CheckCircle className="mr-2" />
                                    Complete Maintenance Work
                                </Button>
                            )}

                        {(!incident.maintenance_record_id ||
                            (maintenance &&
                                maintenance.status === "completed")) &&
                            !showResolveForm && (
                                <Button
                                    className="w-full bg-green-600"
                                    onClick={() => setShowResolveForm(true)}
                                >
                                    <CheckCircle className="mr-2" />
                                    Resolve Incident
                                </Button>
                            )}
                    </>
                )}

                {showCompleteForm && (
                    <form
                        onSubmit={handleComplete}
                        className="bg-slate-50 p-4 rounded border space-y-4"
                    >
                        <h3 className="font-semibold">Completion Details</h3>
                        <div>
                            <Label htmlFor="work-performed-maintenance">
                                Work Performed *
                            </Label>
                            <Textarea
                                id="work-performed-maintenance"
                                required
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="Describe work performed, parts replaced, issues found..."
                                rows={5}
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                Required: Describe the work that was performed.
                            </p>
                        </div>
                        <div>
                            <Label>Total Cost ($)</Label>
                            <Input
                                type="number"
                                min="0"
                                step="0.01"
                                value={cost}
                                onChange={(e) => setCost(e.target.value)}
                                placeholder="0.00"
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                Leave 0 if no separate costs.
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                type="button"
                                variant="outline"
                                className="flex-1"
                                onClick={() => setShowCompleteForm(false)}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                className="flex-1"
                                disabled={completeMutation.isPending}
                            >
                                {completeMutation.isPending && (
                                    <Loader2 className="animate-spin mr-2" />
                                )}
                                Submit
                            </Button>
                        </div>
                    </form>
                )}

                {/* Resolve Incident Form */}
                {showResolveForm && (
                    <form
                        onSubmit={handleResolveIncident}
                        className="bg-slate-50 p-4 rounded border space-y-4 mt-4"
                    >
                        <h3 className="font-semibold">Resolve Incident</h3>
                        <div>
                            <Label htmlFor="resolution-type">
                                Resolution Type
                            </Label>
                            <select
                                id="resolution-type"
                                value={resolutionType}
                                onChange={(e) =>
                                    setResolutionType(e.target.value as any)
                                }
                                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                            >
                                <option value="fixed">Fixed</option>
                                <option value="duplicate">Duplicate</option>
                                <option value="invalid">Invalid</option>
                                <option value="deferred">Deferred</option>
                            </select>
                        </div>
                        <div>
                            <Label htmlFor="resolve-notes">
                                Resolution Notes *
                            </Label>
                            <Textarea
                                id="resolve-notes"
                                required
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="Describe how the incident was resolved..."
                                rows={5}
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button
                                type="button"
                                variant="outline"
                                className="flex-1"
                                onClick={() => {
                                    setShowResolveForm(false);
                                    setNotes("");
                                }}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                className="flex-1 bg-green-600 hover:bg-green-700"
                                disabled={
                                    resolveIncidentMutation.isPending ||
                                    !notes.trim()
                                }
                            >
                                {resolveIncidentMutation.isPending && (
                                    <Loader2 className="animate-spin mr-2 h-4 w-4" />
                                )}
                                Submit Resolution
                            </Button>
                        </div>
                    </form>
                )}

                {incident.status === "resolved" && (
                    <div className="bg-green-50 p-4 rounded border border-green-200 text-green-800 text-center">
                        <CheckCircle className="mx-auto h-8 w-8 mb-2" />
                        <p className="font-semibold">Incident Resolved</p>
                        {incident.resolution_notes && (
                            <p className="text-sm mt-1">
                                {incident.resolution_notes}
                            </p>
                        )}
                    </div>
                )}

                {incident.status === "waiting_approval" && (
                    <div className="bg-yellow-50 p-4 rounded border border-yellow-200 text-yellow-800 text-center">
                        <Clock className="mx-auto h-8 w-8 mb-2 opacity-50" />
                        <p className="font-semibold">
                            Waiting for Admin Approval
                        </p>
                        <p className="text-sm">
                            Work completed. Pending cost approval.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
