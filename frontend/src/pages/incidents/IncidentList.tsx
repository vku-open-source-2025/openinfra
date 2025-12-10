import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { incidentsApi } from "../../api/incidents";
import { IncidentCard } from "../../components/incidents/IncidentCard";
import { IncidentFilters } from "../../components/incidents/IncidentFilters";
import { Pagination } from "../../components/ui/pagination";
import { Skeleton } from "../../components/ui/skeleton";
import { Button } from "../../components/ui/button";
import { Plus, AlertTriangle } from "lucide-react";

type MainTab = "all" | "spam_risk" | "useful" | "duplicates";

const IncidentList: React.FC = () => {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [severity, setSeverity] = useState<string>("");
    const [search, setSearch] = useState<string>("");
    const [day, setDay] = useState<string>("");

    // Simplified main tabs focused on triage
    const [mainTab, setMainTab] = useState<MainTab>("all");

    // Fetch a larger batch (API cap 100), paginate client-side with smaller pageSize
    const fetchLimit = 100;
    const pageSize = 5;

    // Build query params based on selected tabs
    const getQueryParams = () => {
        const params: any = {
            skip: 0,
            limit: fetchLimit,
            severity: severity || undefined,
        };

        // We fetch broadly and filter on the client so we can slice by AI
        // confidence and duplicate tagging without extra backend calls.
        return params;
    };

    const {
        data: incidents,
        isLoading,
        error,
    } = useQuery({
        queryKey: [
            "incidents",
            mainTab,
            severity,
            day,
        ],
        queryFn: () => incidentsApi.list(getQueryParams()),
    });

    // Filter incidents based on simplified tabs
    const filterIncidents = (data: typeof incidents) => {
        if (!data) return [];

        let filtered = data;

        if (mainTab === "spam_risk") {
            // Low AI trust score (<50%) = potential spam/abuse
            filtered = filtered.filter(
                (inc) =>
                    inc.ai_confidence_score !== null &&
                    inc.ai_confidence_score !== undefined &&
                    inc.ai_confidence_score < 0.5
            );
        } else if (mainTab === "useful") {
            // Useful = good AI score or unscored but not marked as spam
            filtered = filtered.filter(
                (inc) =>
                    inc.ai_confidence_score === null ||
                    inc.ai_confidence_score === undefined ||
                    inc.ai_confidence_score >= 0.5
            );
        } else if (mainTab === "duplicates") {
            // Duplicates = explicitly tagged as duplicate in resolution_type
            filtered = filtered.filter(
                (inc) => inc.resolution_type === "duplicate"
            );
        }

        // Filter by specific day (local time)
        if (day) {
            const start = new Date(day);
            const end = new Date(day);
            end.setDate(end.getDate() + 1);

            filtered = filtered.filter((inc) => {
                const created = inc.created_at
                    ? new Date(inc.created_at)
                    : null;
                return (
                    created &&
                    !Number.isNaN(created.getTime()) &&
                    created >= start &&
                    created < end
                );
            });
        }

        // Apply search filter
        if (search) {
            const searchLower = search.toLowerCase();
            filtered = filtered.filter(
                (inc) =>
                    inc.title.toLowerCase().includes(searchLower) ||
                    inc.description.toLowerCase().includes(searchLower) ||
                    inc.location?.address
                        ?.toLowerCase()
                        .includes(searchLower) ||
                    inc.asset?.name?.toLowerCase().includes(searchLower) ||
                    inc.asset?.asset_code
                        ?.toLowerCase()
                        .includes(searchLower) ||
                    inc.asset?.feature_type?.toLowerCase().includes(searchLower)
            );
        }

        return filtered;
    };

    const filteredIncidents = filterIncidents(incidents);
    const totalPages = filteredIncidents
        ? Math.max(1, Math.ceil(filteredIncidents.length / pageSize))
        : 1;
    const safePage = Math.min(page, totalPages || 1);
    const pagedIncidents = filteredIncidents?.slice(
        (safePage - 1) * pageSize,
        safePage * pageSize
    );

    if (error) {
        return (
            <div className="p-8 text-center text-red-500">
                Error loading incidents. Please try again.
            </div>
        );
    }

    const mainTabs: { value: MainTab; label: string; helper?: string }[] = [
        { value: "all", label: "Tất cả" },
        {
            value: "spam_risk",
            label: "Rủi ro spam",
            helper: "Điểm AI < 50%",
        },
        {
            value: "useful",
            label: "Báo cáo hữu ích",
            helper: "Có khả năng hợp lệ",
        },
        {
            value: "duplicates",
            label: "Trùng lặp",
            helper: "Được đánh dấu trùng lặp",
        },
    ];

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                        Sự cố
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Quản lý và theo dõi các sự cố đã báo
                    </p>
                </div>
                <Button
                    onClick={() => navigate({ to: "/admin/incidents/create" })}
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Báo sự cố
                </Button>
            </div>

            <IncidentFilters
                status=""
                severity={severity}
                search={search}
                day={day}
                onStatusChange={() => {}}
                onSeverityChange={setSeverity}
                onSearchChange={setSearch}
                onDayChange={(value) => {
                    setDay(value);
                    setPage(1);
                }}
            />

            {/* Main Category Tabs */}
            <div className="border-b border-slate-200">
                <div className="flex gap-1">
                    {mainTabs.map((tab) => (
                        <button
                            key={tab.value}
                            onClick={() => {
                                setMainTab(tab.value);
                                setPage(1);
                            }}
                            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                                mainTab === tab.value
                                    ? "border-blue-600 text-blue-600"
                                    : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* AI guidance for spam/quality buckets */}
            {mainTab !== "all" && (
                <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-amber-800">
                        <strong>Chỉ mang tính hướng dẫn bởi AI</strong>
                        <p className="mt-1">
                            Những danh mục này dựa trên điểm và nhãn của AI. Vui
                            lòng xem xét sự cố trước khi thực hiện hành động.
                        </p>
                    </div>
                </div>
            )}

            {isLoading ? (
                <div className="space-y-4">
                    {[...Array(5)].map((_, i) => (
                        <Skeleton key={i} className="h-32 w-full" />
                    ))}
                </div>
            ) : filteredIncidents && filteredIncidents.length > 0 ? (
                <>
                    <div className="space-y-4">
                        {pagedIncidents?.map((incident) => (
                            <IncidentCard
                                key={incident.id}
                                incident={incident}
                                onClick={() =>
                                    navigate({
                                        to: `/admin/incidents/${incident.id}`,
                                    })
                                }
                            />
                        ))}
                    </div>
                    <Pagination
                        currentPage={safePage}
                        totalPages={totalPages}
                        onPageChange={setPage}
                    />
                </>
            ) : (
                <div className="text-center py-12 text-slate-500">
                    <p>Không tìm thấy sự cố.</p>
                </div>
            )}
        </div>
    );
};

export default IncidentList;
