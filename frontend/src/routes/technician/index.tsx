import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { incidentsApi } from "../../api/incidents";
import { maintenanceApi } from "../../api/maintenance";
import { useAuthStore } from "../../stores/authStore";
import { IncidentCard } from "../../components/incidents/IncidentCard";
import { MaintenanceCard } from "../../components/maintenance/MaintenanceCard";
import { Loader2, AlertTriangle, Wrench } from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/technician/")({
    component: TechnicianTaskList,
});

type TaskTab = "all" | "incidents" | "maintenance";

function TechnicianTaskList() {
    const { user } = useAuthStore();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<TaskTab>("all");

    // Fetch assigned incidents (investigating status means assigned to technician)
    const { data: allMyIncidents, isLoading: loadingIncidents } = useQuery({
        queryKey: ["my-incidents", user?.id],
        queryFn: async () => {
            const tasks = await incidentsApi.list({ assigned_to: user?.id });
            // Show incidents that are assigned/investigating or resolved (waiting approval)
            return tasks.filter((t) =>
                ["investigating", "resolved", "waiting_approval"].includes(
                    t.status
                )
            );
        },
        enabled: !!user?.id,
    });

    // Fetch assigned maintenance work orders
    const { data: allMyMaintenance, isLoading: loadingMaintenance } = useQuery({
        queryKey: ["my-maintenance", user?.id],
        queryFn: async () => {
            return await maintenanceApi.list({ assigned_to: user?.id });
        },
        enabled: !!user?.id,
    });

    const isLoading = loadingIncidents || loadingMaintenance;

    // Filter maintenance by active statuses
    const activeMaintenance =
        allMyMaintenance?.filter((m) =>
            ["scheduled", "in_progress"].includes(m.status)
        ) || [];

    const allTasks = [
        ...(allMyIncidents || []).map((inc) => ({
            type: "incident" as const,
            data: inc,
        })),
        ...(activeMaintenance || []).map((maint) => ({
            type: "maintenance" as const,
            data: maint,
        })),
    ].sort((a, b) => {
        // Sort by created_at or scheduled_date
        const dateA =
            a.type === "incident"
                ? new Date(a.data.created_at).getTime()
                : new Date(a.data.scheduled_date).getTime();
        const dateB =
            b.type === "incident"
                ? new Date(b.data.created_at).getTime()
                : new Date(b.data.scheduled_date).getTime();
        return dateB - dateA; // Newest first
    });

    const filteredTasks =
        activeTab === "all"
            ? allTasks
            : activeTab === "incidents"
            ? allTasks.filter((t) => t.type === "incident")
            : allTasks.filter((t) => t.type === "maintenance");

    if (isLoading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-xl">My Tasks</h2>
                <div className="flex items-center gap-2 text-sm">
                    <span className="text-slate-600">
                        {allMyIncidents?.length || 0} incidents,{" "}
                        {activeMaintenance.length} maintenance
                    </span>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-2 border-b border-slate-200">
                <button
                    onClick={() => setActiveTab("all")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === "all"
                            ? "border-blue-600 text-blue-600"
                            : "border-transparent text-slate-500 hover:text-slate-700"
                    }`}
                >
                    All Tasks
                </button>
                <button
                    onClick={() => setActiveTab("incidents")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === "incidents"
                            ? "border-blue-600 text-blue-600"
                            : "border-transparent text-slate-500 hover:text-slate-700"
                    }`}
                >
                    <AlertTriangle className="inline h-4 w-4 mr-1" />
                    Incidents ({allMyIncidents?.length || 0})
                </button>
                <button
                    onClick={() => setActiveTab("maintenance")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === "maintenance"
                            ? "border-blue-600 text-blue-600"
                            : "border-transparent text-slate-500 hover:text-slate-700"
                    }`}
                >
                    <Wrench className="inline h-4 w-4 mr-1" />
                    Maintenance ({activeMaintenance.length})
                </button>
            </div>

            {filteredTasks.length > 0 ? (
                <div className="space-y-4">
                    {filteredTasks.map((task) => {
                        if (task.type === "incident") {
                            return (
                                <div
                                    key={task.data.id}
                                    onClick={() =>
                                        navigate({
                                            to: `/technician/tasks/${task.data.id}`,
                                        })
                                    }
                                >
                                    <IncidentCard incident={task.data} />
                                </div>
                            );
                        } else {
                            return (
                                <div
                                    key={task.data.id}
                                    onClick={() =>
                                        navigate({
                                            to: `/technician/maintenance/${task.data.id}`,
                                        })
                                    }
                                >
                                    <MaintenanceCard maintenance={task.data} />
                                </div>
                            );
                        }
                    })}
                </div>
            ) : (
                <div className="text-center p-8 text-slate-500 bg-white rounded-lg border border-slate-200">
                    <p>
                        {activeTab === "all" &&
                            "No active tasks assigned to you."}
                        {activeTab === "incidents" &&
                            "No active incidents assigned to you."}
                        {activeTab === "maintenance" &&
                            "No active maintenance work orders assigned to you."}
                    </p>
                </div>
            )}
        </div>
    );
}
