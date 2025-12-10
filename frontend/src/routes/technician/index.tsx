import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { incidentsApi } from "../../api/incidents";
import { maintenanceApi } from "../../api/maintenance";
import { useAuthStore } from "../../stores/authStore";
import { IncidentCard } from "../../components/incidents/IncidentCard";
import { MaintenanceCard } from "../../components/maintenance/MaintenanceCard";
import { Loader2, Search, AlertTriangle, Wrench } from "lucide-react";
import { useState } from "react";
import { Input } from "../../components/ui/input";
import { Select } from "../../components/ui/select";

export const Route = createFileRoute("/technician/")({
    component: TechnicianTaskList,
});

function TechnicianTaskList() {
    const { user } = useAuthStore();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<"all" | "incidents" | "maintenance">("all");
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("");
    const [severityFilter, setSeverityFilter] = useState<string>("");

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

    // Apply filters
    let filteredTasks = allTasks;

    // Filter by active tab
    if (activeTab === "incidents") {
        filteredTasks = filteredTasks.filter((t) => t.type === "incident");
    } else if (activeTab === "maintenance") {
        filteredTasks = filteredTasks.filter((t) => t.type === "maintenance");
    }
    // activeTab === "all" shows all tasks

    // Filter by status
    if (statusFilter) {
        filteredTasks = filteredTasks.filter((t) => {
            if (t.type === "incident") {
                return t.data.status === statusFilter;
            } else {
                return t.data.status === statusFilter;
            }
        });
    }

    // Filter by severity (only for incidents)
    if (severityFilter) {
        filteredTasks = filteredTasks.filter((t) => {
            if (t.type === "incident") {
                return t.data.severity === severityFilter;
            }
            // Maintenance tasks don't have severity, so they're excluded when severity filter is active
            return false;
        });
    }

    // Filter by search
    if (search) {
        const searchLower = search.toLowerCase();
        filteredTasks = filteredTasks.filter((t) => {
            if (t.type === "incident") {
                return (
                    t.data.title?.toLowerCase().includes(searchLower) ||
                    t.data.description?.toLowerCase().includes(searchLower) ||
                    t.data.incident_number?.toLowerCase().includes(searchLower)
                );
            } else {
                return (
                    t.data.title?.toLowerCase().includes(searchLower) ||
                    t.data.description?.toLowerCase().includes(searchLower) ||
                    t.data.work_order_number?.toLowerCase().includes(searchLower)
                );
            }
        });
    }

    if (isLoading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-xl">Công việc của tôi</h2>
                <div className="flex items-center gap-2 text-sm">
                    <span className="text-slate-600">
                        {filteredTasks.length} / {allTasks.length} công việc
                    </span>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-2 border-b border-slate-200 mb-4">
                <button
                    onClick={() => setActiveTab("all")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === "all"
                            ? "border-blue-600 text-blue-600"
                            : "border-transparent text-slate-500 hover:text-slate-700"
                    }`}
                >
                    Tất cả công việc
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
                    Sự cố ({allMyIncidents?.length || 0})
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
                    Bảo trì ({activeMaintenance.length})
                </button>
            </div>

            {/* Search and Filters */}
            <div className="bg-white p-4 rounded-lg border border-slate-200 mb-4">
                <div className="flex flex-wrap gap-4">
                    <div className="flex-1 min-w-[200px]">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                            <Input
                                placeholder="Tìm kiếm tasks..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="pl-10"
                            />
                        </div>
                    </div>
                    <div className="w-[180px]">
                        <Select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            placeholder="Tất cả trạng thái"
                        >
                            <option value="investigating">Đang điều tra</option>
                            <option value="resolved">Đã giải quyết</option>
                            <option value="waiting_approval">Chờ phê duyệt</option>
                            <option value="scheduled">Đã lên lịch</option>
                            <option value="in_progress">Đang thực hiện</option>
                            <option value="completed">Hoàn thành</option>
                        </Select>
                    </div>
                    <div className="w-[180px]">
                        <Select
                            value={severityFilter}
                            onChange={(e) => setSeverityFilter(e.target.value)}
                            placeholder="Tất cả mức độ"
                        >
                            <option value="low">Thấp</option>
                            <option value="medium">Trung bình</option>
                            <option value="high">Cao</option>
                            <option value="critical">Nghiêm trọng</option>
                        </Select>
                    </div>
                </div>
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
                        {search || statusFilter || severityFilter
                            ? "Không có công việc nào khớp với bộ lọc của bạn."
                            : activeTab === "all"
                            ? "Không có công việc nào được phân công cho bạn."
                            : activeTab === "incidents"
                            ? "Không có sự cố nào được phân công cho bạn."
                            : "Không có lệnh bảo trì nào được phân công cho bạn."}
                    </p>
                </div>
            )}
        </div>
    );
}
