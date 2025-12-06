import { useState, lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "@tanstack/react-router";
import { assetsApi } from "../../api/assets";
import {
    Tabs,
    TabsList,
    TabsTrigger,
    TabsContent,
} from "../../components/ui/tabs";
import { Button } from "../../components/ui/button";
import { Skeleton } from "../../components/ui/skeleton";
import {
    ArrowLeft,
    MapPin,
    TrendingUp,
    Edit,
    Plus,
    AlertTriangle,
    Map,
} from "lucide-react";
import {
    getHealthScoreColor,
    getHealthScoreLabel,
} from "../../utils/healthScore";
import { format } from "date-fns";

// Lazy load tab components
const AssetOverviewTab = lazy(
    () => import("../../components/assets/AssetOverviewTab")
);
const MaintenanceHistoryTab = lazy(
    () => import("../../components/assets/MaintenanceHistoryTab")
);
const AssetIncidentsTab = lazy(
    () => import("../../components/assets/AssetIncidentsTab")
);
const PreventiveMaintenanceTab = lazy(
    () => import("../../components/assets/PreventiveMaintenanceTab")
);
const LifecycleConditionTab = lazy(
    () => import("../../components/assets/LifecycleConditionTab")
);
const AssetDocumentsTab = lazy(
    () => import("../../components/assets/AssetDocumentsTab")
);
const AssetReportsTab = lazy(
    () => import("../../components/assets/AssetReportsTab")
);
const AssetSensorsTab = lazy(
    () => import("../../components/assets/AssetSensorsTab")
);

const AssetDetail: React.FC = () => {
    const { id } = useParams({ from: "/admin/assets/$id" });
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState("overview");

    const {
        data: asset,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["asset", id],
        queryFn: () => assetsApi.getById(id),
        enabled: !!id,
    });

    if (isLoading) {
        return (
            <div className="p-6 space-y-6">
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-96 w-full" />
            </div>
        );
    }

    if (error || !asset) {
        return (
            <div className="p-6">
                <div className="text-center py-12">
                    <p className="text-red-500 mb-4">
                        Error loading asset details
                    </p>
                    <Button onClick={() => navigate({ to: "/admin/assets" })}>
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back to Assets
                    </Button>
                </div>
            </div>
        );
    }

    const healthScore = asset.lifecycle?.health_score ?? 0;
    const healthColor = getHealthScoreColor(healthScore);
    const healthLabel = getHealthScoreLabel(healthScore);
    // Use asset.status since lifecycle data may not be available from API
    const lifecycleStatus =
        asset.lifecycle?.lifecycle_status ?? asset.status ?? "active";

    const getStatusBadgeColor = (status: string) => {
        switch (status) {
            case "operational":
            case "active":
                return "bg-green-100 text-green-700";
            case "under_repair":
            case "maintenance":
                return "bg-yellow-100 text-yellow-700";
            case "damaged":
                return "bg-red-100 text-red-700";
            case "decommissioned":
            case "inactive":
                return "bg-gray-100 text-gray-700";
            default:
                return "bg-slate-100 text-slate-700";
        }
    };

    return (
        <div className="p-6 space-y-6">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm text-slate-500">
                <button
                    onClick={() => navigate({ to: "/admin" })}
                    className="hover:text-slate-900"
                >
                    Home
                </button>
                <span>/</span>
                <button
                    onClick={() => navigate({ to: "/admin" })}
                    className="hover:text-slate-900"
                >
                    Assets
                </button>
                <span>/</span>
                <span className="text-slate-900 font-medium">
                    {asset.name || asset.feature_code}
                </span>
            </div>

            {/* Asset Header */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-start justify-between mb-6">
                    <div className="flex items-start gap-4">
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-2xl font-bold text-slate-900">
                                    {asset.name || asset.feature_type}
                                </h1>
                                <span
                                    className={`px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wide ${getStatusBadgeColor(
                                        lifecycleStatus
                                    )}`}
                                >
                                    {lifecycleStatus.replace("_", " ")}
                                </span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-slate-600">
                                <div>
                                    <span className="font-medium">
                                        Asset ID:
                                    </span>{" "}
                                    {asset.id.slice(-8)}
                                </div>
                                {asset.geometry?.coordinates &&
                                    Array.isArray(asset.geometry.coordinates) &&
                                    asset.geometry.coordinates.length >= 2 &&
                                    typeof asset.geometry.coordinates[0] ===
                                        "number" &&
                                    typeof asset.geometry.coordinates[1] ===
                                        "number" && (
                                        <div className="flex items-center gap-1">
                                            <MapPin size={14} />
                                            <span>
                                                {asset.geometry.coordinates[1].toFixed(
                                                    6
                                                )}
                                                ,{" "}
                                                {asset.geometry.coordinates[0].toFixed(
                                                    6
                                                )}
                                            </span>
                                        </div>
                                    )}
                                {asset.location?.address &&
                                    !asset.geometry?.coordinates && (
                                        <div className="flex items-center gap-1">
                                            <MapPin size={14} />
                                            <span>
                                                {asset.location.address}
                                            </span>
                                        </div>
                                    )}
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={() =>
                                navigate({
                                    to: "/admin/map",
                                    search: { assetId: id },
                                })
                            }
                        >
                            <Map className="h-4 w-4 mr-2" />
                            View on Map
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => navigate({ to: "/admin" })}
                        >
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back
                        </Button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-xs text-slate-500 mb-1">
                            Last Maintenance
                        </div>
                        <div className="text-sm font-semibold text-slate-900">
                            {asset.lifecycle?.last_maintenance_date
                                ? format(
                                      new Date(
                                          asset.lifecycle.last_maintenance_date
                                      ),
                                      "dd/MM/yyyy"
                                  )
                                : "N/A"}
                        </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-xs text-slate-500 mb-1">
                            Next Maintenance
                        </div>
                        <div className="text-sm font-semibold text-slate-900">
                            {asset.lifecycle?.next_maintenance_date
                                ? format(
                                      new Date(
                                          asset.lifecycle.next_maintenance_date
                                      ),
                                      "dd/MM/yyyy"
                                  )
                                : "Not scheduled"}
                        </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-xs text-slate-500 mb-1">
                            Health Score
                        </div>
                        <div className="flex items-center gap-2">
                            <span
                                className={`text-lg font-bold ${
                                    healthColor === "green"
                                        ? "text-green-600"
                                        : healthColor === "yellow"
                                        ? "text-yellow-600"
                                        : healthColor === "orange"
                                        ? "text-orange-600"
                                        : "text-red-600"
                                }`}
                            >
                                {healthScore}/100
                            </span>
                            <TrendingUp size={16} className="text-slate-400" />
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                            {healthLabel}
                        </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-xs text-slate-500 mb-1">
                            Remaining Life
                        </div>
                        <div className="text-sm font-semibold text-slate-900">
                            {asset.lifecycle?.remaining_lifespan_years
                                ? `${asset.lifecycle.remaining_lifespan_years} years`
                                : "N/A"}
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="flex flex-wrap gap-2">
                    <Button
                        onClick={() => {
                            // TODO: Navigate to maintenance create with asset_id
                            console.log("Add maintenance for asset:", id);
                        }}
                    >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Maintenance Record
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() =>
                            navigate({ to: "/admin/incidents/create" })
                        }
                    >
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Report Incident
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => {
                            // TODO: Navigate to asset edit
                            console.log("Edit asset:", id);
                        }}
                    >
                        <Edit className="h-4 w-4 mr-2" />
                        Edit Asset
                    </Button>
                </div>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="mb-6">
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="sensors">Sensors</TabsTrigger>
                        <TabsTrigger value="maintenance">
                            Maintenance History
                        </TabsTrigger>
                        <TabsTrigger value="incidents">Incidents</TabsTrigger>
                        <TabsTrigger value="preventive">
                            Preventive Maintenance
                        </TabsTrigger>
                        <TabsTrigger value="lifecycle">
                            Lifecycle & Condition
                        </TabsTrigger>
                        <TabsTrigger value="documents">Documents</TabsTrigger>
                        <TabsTrigger value="reports">Reports</TabsTrigger>
                    </TabsList>

                    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
                        <TabsContent value="overview">
                            <AssetOverviewTab assetId={id} asset={asset} />
                        </TabsContent>
                        <TabsContent value="sensors">
                            <AssetSensorsTab assetId={id} />
                        </TabsContent>
                        <TabsContent value="maintenance">
                            <MaintenanceHistoryTab assetId={id} />
                        </TabsContent>
                        <TabsContent value="incidents">
                            <AssetIncidentsTab assetId={id} />
                        </TabsContent>
                        <TabsContent value="preventive">
                            <PreventiveMaintenanceTab assetId={id} />
                        </TabsContent>
                        <TabsContent value="lifecycle">
                            <LifecycleConditionTab assetId={id} asset={asset} />
                        </TabsContent>
                        <TabsContent value="documents">
                            <AssetDocumentsTab assetId={id} />
                        </TabsContent>
                        <TabsContent value="reports">
                            <AssetReportsTab assetId={id} />
                        </TabsContent>
                    </Suspense>
                </Tabs>
            </div>
        </div>
    );
};

export default AssetDetail;
