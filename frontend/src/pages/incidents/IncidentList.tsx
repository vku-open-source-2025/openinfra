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

type MainTab = "open" | "to_verify" | "closed" | "all";
type VerifySubTab = "all" | "spam_risk" | "safe";
type ClosedSubTab = "all" | "rejected" | "resolved";

const IncidentList: React.FC = () => {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [severity, setSeverity] = useState<string>("");
    const [search, setSearch] = useState<string>("");

    // Main tabs
    const [mainTab, setMainTab] = useState<MainTab>("open");
    // Sub-tabs for "To Verify"
    const [verifySubTab, setVerifySubTab] = useState<VerifySubTab>("all");
    // Sub-tabs for "Closed"
    const [closedSubTab, setClosedSubTab] = useState<ClosedSubTab>("all");

    const limit = 99;

    // Build query params based on selected tabs
    const getQueryParams = () => {
        const params: any = {
            skip: (page - 1) * limit,
            limit,
            severity: severity || undefined,
        };

        switch (mainTab) {
            case "open":
                // Open tickets: not closed, not resolved
                // We'll filter on frontend since backend may not support complex status filtering
                params.status = undefined; // Get all and filter
                break;
            case "to_verify":
                params.verification_status = "to_be_verified";
                break;
            case "closed":
                params.status = "closed";
                break;
            case "all":
                // No filter
                break;
        }

        return params;
    };

    const {
        data: incidents,
        isLoading,
        error,
    } = useQuery({
        queryKey: [
            "incidents",
            page,
            mainTab,
            verifySubTab,
            closedSubTab,
            severity,
        ],
        queryFn: () => incidentsApi.list(getQueryParams()),
    });

    // Filter incidents based on tabs
    const filterIncidents = (data: typeof incidents) => {
        if (!data) return [];

        let filtered = data;

        // Apply main tab filter
        if (mainTab === "open") {
            // Open = not closed and not resolved
            filtered = filtered.filter(
                (inc) => inc.status !== "closed" && inc.status !== "resolved"
            );
        }

        // Apply sub-tab filters
        if (mainTab === "to_verify") {
            // Filter by AI verification confidence
            if (verifySubTab === "spam_risk") {
                // Low confidence = potential spam (< 0.5)
                filtered = filtered.filter(
                    (inc) =>
                        inc.ai_confidence_score !== null &&
                        inc.ai_confidence_score !== undefined &&
                        inc.ai_confidence_score < 0.5
                );
            } else if (verifySubTab === "safe") {
                // Higher confidence = probably safe (>= 0.5)
                filtered = filtered.filter(
                    (inc) =>
                        inc.ai_confidence_score === null ||
                        inc.ai_confidence_score === undefined ||
                        inc.ai_confidence_score >= 0.5
                );
            }
        }

        if (mainTab === "closed") {
            if (closedSubTab === "rejected") {
                // Rejected = resolution_type is not_an_issue
                filtered = filtered.filter(
                    (inc) => inc.resolution_type === "not_an_issue"
                );
            } else if (closedSubTab === "resolved") {
                // Resolved = resolution_type is fixed, duplicate, etc.
                filtered = filtered.filter(
                    (inc) =>
                        inc.resolution_type &&
                        inc.resolution_type !== "not_an_issue"
                );
            }
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
        ? Math.ceil(filteredIncidents.length / limit)
        : 1;

    if (error) {
        return (
            <div className="p-8 text-center text-red-500">
                Error loading incidents. Please try again.
            </div>
        );
    }

    const mainTabs: { value: MainTab; label: string; count?: number }[] = [
        { value: "open", label: "Open" },
        { value: "to_verify", label: "To Verify" },
        { value: "closed", label: "Closed" },
        { value: "all", label: "All" },
    ];

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                        Incidents
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Manage and track reported incidents
                    </p>
                </div>
                <Button
                    onClick={() => navigate({ to: "/admin/incidents/create" })}
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Report Incident
                </Button>
            </div>

            <IncidentFilters
                status=""
                severity={severity}
                search={search}
                onStatusChange={() => {}}
                onSeverityChange={setSeverity}
                onSearchChange={setSearch}
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

            {/* Sub-tabs for "To Verify" with AI warning */}
            {mainTab === "to_verify" && (
                <div className="space-y-3">
                    <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-amber-800">
                            <strong>AI Verification Results</strong>
                            <p className="mt-1">
                                These results are generated by AI and may
                                contain errors. Please review each incident
                                carefully before taking action.
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        {[
                            { value: "all" as VerifySubTab, label: "All" },
                            {
                                value: "spam_risk" as VerifySubTab,
                                label: "🚨 Spam Risk",
                                className: "text-red-600",
                            },
                            {
                                value: "safe" as VerifySubTab,
                                label: "✅ Likely Safe",
                                className: "text-green-600",
                            },
                        ].map((tab) => (
                            <button
                                key={tab.value}
                                onClick={() => {
                                    setVerifySubTab(tab.value);
                                    setPage(1);
                                }}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                                    verifySubTab === tab.value
                                        ? "bg-slate-800 text-white"
                                        : `bg-slate-100 hover:bg-slate-200 ${
                                              tab.className || "text-slate-600"
                                          }`
                                }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Sub-tabs for "Closed" */}
            {mainTab === "closed" && (
                <div className="flex gap-2">
                    {[
                        { value: "all" as ClosedSubTab, label: "All Closed" },
                        {
                            value: "rejected" as ClosedSubTab,
                            label: "❌ Rejected",
                        },
                        {
                            value: "resolved" as ClosedSubTab,
                            label: "✓ Resolved",
                        },
                    ].map((tab) => (
                        <button
                            key={tab.value}
                            onClick={() => {
                                setClosedSubTab(tab.value);
                                setPage(1);
                            }}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                                closedSubTab === tab.value
                                    ? "bg-slate-800 text-white"
                                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
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
                        {filteredIncidents.map((incident) => (
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
                    {totalPages > 1 && (
                        <Pagination
                            currentPage={page}
                            totalPages={totalPages}
                            onPageChange={setPage}
                        />
                    )}
                </>
            ) : (
                <div className="text-center py-12 text-slate-500">
                    <p>No incidents found.</p>
                </div>
            )}
        </div>
    );
};

export default IncidentList;
