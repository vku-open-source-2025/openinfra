import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "@tanstack/react-router";
import { format } from "date-fns";
import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    Building2,
    Calendar,
    ExternalLink,
    FileText,
    MapPin,
    Tag,
    TrendingUp,
} from "lucide-react";
import React from "react";
import type { Asset as ApiAsset } from "../api";
import { getMaintenanceLogs } from "../api";
import { assetsApi } from "../api/assets";
import { publicApi } from "../api/public";
import Header from "../components/Header";
import MaintenanceLogList from "../components/MaintenanceLog";
import MapComponent from "../components/Map";
import ReportModal from "../components/ReportModal";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import type { Asset } from "../types/asset";

const AssetDetailPage: React.FC = () => {
    const { id } = useParams({ from: "/asset/$id" });
    const navigate = useNavigate();
    const [showMap, setShowMap] = React.useState(false);
    const [showReportModal, setShowReportModal] = React.useState(false);

    // Try to fetch asset by ID first, then by code if that fails
    const {
        data: asset,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["asset", id],
        queryFn: async () => {
            try {
                // First try to get by ID (authenticated endpoint)
                return await assetsApi.getById(id);
            } catch (err) {
                // If that fails, try public API by code
                try {
                    const publicAsset = await publicApi.getPublicAsset(id);
                    // Convert public asset to full asset format
                    return {
                        id: id,
                        asset_code: publicAsset.asset_code,
                        name: publicAsset.name,
                        feature_type: publicAsset.feature_type,
                        feature_code: publicAsset.asset_code,
                        category: publicAsset.category,
                        status: publicAsset.status,
                        location: publicAsset.location,
                        geometry: {
                            type: "Point" as const,
                            coordinates: [
                                publicAsset.location.coordinates.longitude,
                                publicAsset.location.coordinates.latitude,
                            ],
                        },
                        created_at: "",
                        updated_at: "",
                    } as Asset;
                } catch (publicErr) {
                    throw err; // Throw original error
                }
            }
        },
        enabled: !!id,
    });

    const { data: maintenanceLogs } = useQuery({
        queryKey: ["maintenance", id],
        queryFn: () => getMaintenanceLogs(id),
        enabled: !!id && !!asset,
    });

    if (isLoading) {
        return (
            <div className="flex flex-col h-screen bg-slate-50">
                <Header />
                <div className="flex-1 p-6 space-y-6 mt-20">
                    <Skeleton className="h-32 w-full" />
                    <Skeleton className="h-96 w-full" />
                </div>
            </div>
        );
    }

    if (error || !asset) {
        return (
            <div className="flex flex-col h-screen bg-slate-50">
                <Header />
                <div className="flex-1 flex items-center justify-center mt-20">
                    <div className="text-center p-8">
                        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                        <h2 className="text-xl font-bold text-slate-900 mb-2">
                            Không tìm thấy tài sản
                        </h2>
                        <p className="text-slate-600 mb-6">
                            The asset you're looking for doesn't exist or is not
                            available.
                        </p>
                        <div className="flex gap-3 justify-center">
                                <Button
                                onClick={() => navigate({ to: "/map" })}
                                variant="outline"
                            >
                                <ArrowLeft className="h-4 w-4 mr-2" />
                                Quay lại bản đồ
                            </Button>
                            <Button onClick={() => navigate({ to: "/" })}>
                                Go Home
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const getStatusBadgeColor = (status: string) => {
        switch (status.toLowerCase()) {
            case "operational":
            case "active":
                return "bg-green-100 text-green-700 border-green-200";
            case "under_repair":
            case "maintenance":
                return "bg-yellow-100 text-yellow-700 border-yellow-200";
            case "damaged":
                return "bg-red-100 text-red-700 border-red-200";
            case "decommissioned":
            case "inactive":
                return "bg-gray-100 text-gray-700 border-gray-200";
            default:
                return "bg-slate-100 text-slate-700 border-slate-200";
        }
    };

    const healthScore = asset.lifecycle?.health_score ?? null;
    const getHealthScoreColor = (score: number | null) => {
        if (score === null) return "text-slate-500";
        if (score >= 80) return "text-green-600";
        if (score >= 60) return "text-yellow-600";
        if (score >= 40) return "text-orange-600";
        return "text-red-600";
    };

    const coordinates =
        asset.geometry?.coordinates &&
        Array.isArray(asset.geometry.coordinates) &&
        asset.geometry.coordinates.length >= 2 &&
        typeof asset.geometry.coordinates[0] === "number" &&
        typeof asset.geometry.coordinates[1] === "number"
            ? {
                  lng: asset.geometry.coordinates[0],
                  lat: asset.geometry.coordinates[1],
              }
            : asset.location?.coordinates
            ? {
                  lng: asset.location.coordinates.longitude,
                  lat: asset.location.coordinates.latitude,
              }
            : null;

    return (
        <div className="flex flex-col min-h-screen bg-slate-50">
            <Header />
            <div className="flex-1 mt-20">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {/* Back Button */}
                    <Button
                        onClick={() => navigate({ to: "/map" })}
                        variant="ghost"
                        className="mb-6"
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Quay lại bản đồ
                    </Button>

                    {/* Asset Header */}
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-3 flex-wrap">
                                    <h1 className="text-3xl font-bold text-slate-900">
                                        {asset.name || asset.feature_type}
                                    </h1>
                                    <span
                                        className={`px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wide border ${getStatusBadgeColor(
                                            asset.lifecycle?.lifecycle_status ||
                                                asset.status ||
                                                "active"
                                        )}`}
                                    >
                                        {(
                                            asset.lifecycle?.lifecycle_status ||
                                            asset.status ||
                                            "active"
                                        ).replace("_", " ")}
                                    </span>
                                </div>
                                <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
                                    {asset.asset_code && (
                                        <div className="flex items-center gap-1">
                                            <Tag size={14} />
                                            <span className="font-mono">
                                                {asset.asset_code}
                                            </span>
                                        </div>
                                    )}
                                    {coordinates && (
                                        <div className="flex items-center gap-1">
                                            <MapPin size={14} />
                                            <span className="font-mono">
                                                {coordinates.lat.toFixed(6)},{" "}
                                                {coordinates.lng.toFixed(6)}
                                            </span>
                                        </div>
                                    )}
                                    {asset.location?.address && (
                                        <div className="flex items-center gap-1">
                                            <Building2 size={14} />
                                            <span>
                                                {asset.location.address}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                            {coordinates && (
                                <Button
                                    onClick={() => setShowMap(!showMap)}
                                    variant="outline"
                                >
                                    <MapPin className="h-4 w-4 mr-2" />
                                    {showMap ? "Ẩn" : "Hiện"} bản đồ
                                </Button>
                            )}
                        </div>

                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {healthScore !== null && (
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                                        Điểm sức khỏe
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span
                                            className={`text-2xl font-bold ${getHealthScoreColor(
                                                healthScore
                                            )}`}
                                        >
                                            {healthScore}/100
                                        </span>
                                        <TrendingUp
                                            size={18}
                                            className="text-slate-400"
                                        />
                                    </div>
                                </div>
                            )}
                            {asset.lifecycle?.last_maintenance_date && (
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                                        Lần bảo trì gần nhất
                                    </div>
                                    <div className="text-sm font-semibold text-slate-900">
                                        {format(
                                            new Date(
                                                asset.lifecycle.last_maintenance_date
                                            ),
                                            "dd/MM/yyyy"
                                        )}
                                    </div>
                                </div>
                            )}
                            {asset.lifecycle?.next_maintenance_date && (
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                                        Bảo trì tiếp theo
                                    </div>
                                    <div className="text-sm font-semibold text-slate-900">
                                        {format(
                                            new Date(
                                                asset.lifecycle.next_maintenance_date
                                            ),
                                            "dd/MM/yyyy"
                                        )}
                                    </div>
                                </div>
                            )}
                            {asset.lifecycle?.remaining_lifespan_years && (
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                                        Thời gian sử dụng còn lại
                                    </div>
                                    <div className="text-sm font-semibold text-slate-900">
                                        {
                                            asset.lifecycle
                                                .remaining_lifespan_years
                                        }{" "}
                                        years
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Map View */}
                    {showMap && coordinates && (
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-6 h-96">
                            <MapComponent
                                assets={[asset]}
                                selectedAsset={asset}
                                className="h-full w-full"
                            />
                        </div>
                    )}

                    {/* Main Content Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Left Column - Main Info */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Basic Information */}
                            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                                <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                                    <FileText size={20} />
                                    Basic Information
                                </h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs text-slate-500 uppercase tracking-wide">
                                            Asset Type
                                        </label>
                                        <p className="text-sm font-medium text-slate-900 mt-1">
                                            {asset.feature_type}
                                        </p>
                                    </div>
                                    {asset.category && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Category
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {asset.category}
                                            </p>
                                        </div>
                                    )}
                                    {asset.feature_code && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Feature Code
                                            </label>
                                            <p className="text-sm font-mono text-slate-900 mt-1">
                                                {asset.feature_code}
                                            </p>
                                        </div>
                                    )}
                                    {asset.managing_unit && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Managing Unit
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {asset.managing_unit}
                                            </p>
                                        </div>
                                    )}
                                    {asset.manufacturer && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Manufacturer
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {asset.manufacturer}
                                            </p>
                                        </div>
                                    )}
                                    {asset.specifications?.model && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Model
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {asset.specifications.model}
                                            </p>
                                        </div>
                                    )}
                                    {asset.lifecycle?.commissioned_date && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Ngày đưa vào hoạt động
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {format(
                                                    new Date(
                                                        asset.lifecycle.commissioned_date
                                                    ),
                                                    "dd/MM/yyyy"
                                                )}
                                            </p>
                                        </div>
                                    )}
                                    {asset.lifecycle
                                        ?.designed_lifespan_years && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Tuổi thọ thiết kế
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {
                                                    asset.lifecycle
                                                        .designed_lifespan_years
                                                }{" "}
                                                years
                                            </p>
                                        </div>
                                    )}
                                    {asset.created_at && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Ngày tạo
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {format(
                                                    new Date(asset.created_at),
                                                    "dd/MM/yyyy"
                                                )}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Location Details */}
                            {asset.location && (
                                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                                    <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                                        <MapPin size={20} />
                                        Thông tin vị trí
                                    </h2>
                                    <div className="space-y-2">
                                        {asset.location.address && (
                                            <div>
                                                <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                    Địa chỉ
                                                </label>
                                                <p className="text-sm font-medium text-slate-900 mt-1">
                                                    {asset.location.address}
                                                </p>
                                            </div>
                                        )}
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            {asset.location.ward && (
                                                <div>
                                                    <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                        Phường/Xã
                                                    </label>
                                                    <p className="text-sm font-medium text-slate-900 mt-1">
                                                        {asset.location.ward}
                                                    </p>
                                                </div>
                                            )}
                                            {asset.location.district && (
                                                <div>
                                                    <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                        Quận/Huyện
                                                    </label>
                                                    <p className="text-sm font-medium text-slate-900 mt-1">
                                                        {
                                                            asset.location
                                                                .district
                                                        }
                                                    </p>
                                                </div>
                                            )}
                                            {asset.location.city && (
                                                <div>
                                                    <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                        Thành phố
                                                    </label>
                                                    <p className="text-sm font-medium text-slate-900 mt-1">
                                                        {asset.location.city}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Maintenance History */}
                            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                                <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                                    <Calendar size={20} />
                                    Maintenance History
                                </h2>
                                {maintenanceLogs &&
                                maintenanceLogs.length > 0 ? (
                                    <MaintenanceLogList assetId={id} />
                                ) : (
                                    <div className="text-center py-8 text-slate-500">
                                        <p>Không có lịch sử bảo trì.</p>
                                    </div>
                                )}
                            </div>

                            {/* Properties */}
                            {asset.properties &&
                                Object.keys(asset.properties).length > 0 && (
                                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                                        <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                                            <Activity size={20} />
                                            Additional Properties
                                        </h2>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {Object.entries(
                                                asset.properties
                                            ).map(([key, value]) => (
                                                <div key={key}>
                                                    <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                        {key.replace(/_/g, " ")}
                                                    </label>
                                                    <p className="text-sm font-medium text-slate-900 mt-1">
                                                        {String(value)}
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                        </div>

                        {/* Right Column - Sidebar */}
                        <div className="space-y-6">
                            {/* Status Card */}
                            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                                <h3 className="text-lg font-semibold text-slate-900 mb-4">
                                    Status
                                </h3>
                                <div className="space-y-3">
                                    <div>
                                        <label className="text-xs text-slate-500 uppercase tracking-wide">
                                            Current Status
                                        </label>
                                        <div className="mt-2">
                                            <span
                                                className={`px-3 py-1 text-xs font-bold rounded-full uppercase ${getStatusBadgeColor(
                                                    asset.lifecycle
                                                        ?.lifecycle_status ||
                                                        asset.status ||
                                                        "active"
                                                )}`}
                                            >
                                                {(
                                                    asset.lifecycle
                                                        ?.lifecycle_status ||
                                                    asset.status ||
                                                    "active"
                                                ).replace("_", " ")}
                                            </span>
                                        </div>
                                    </div>
                                    {asset.condition && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Condition
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {asset.condition}
                                            </p>
                                        </div>
                                    )}
                                    {asset.lifecycle_stage && (
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase tracking-wide">
                                                Lifecycle Stage
                                            </label>
                                            <p className="text-sm font-medium text-slate-900 mt-1">
                                                {asset.lifecycle_stage}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Quick Actions */}
                            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                                <h3 className="text-lg font-semibold text-slate-900 mb-4">
                                    Quick Actions
                                </h3>
                                <div className="flex flex-col gap-2">
                                    <Link to="/map" search={{ assetId: id }}>
                                        <Button
                                            className="w-full"
                                            variant="default"
                                        >
                                            <MapPin className="h-4 w-4 mr-2" />
                                            Xem trên bản đồ
                                        </Button>
                                    </Link>
                                    <Button
                                        className="w-full"
                                        variant="destructive"
                                        onClick={() => setShowReportModal(true)}
                                    >
                                        <AlertTriangle className="h-4 w-4 mr-2" />
                                        Report Incident
                                    </Button>
                                </div>
                            </div>

                            {/* Attachments */}
                            {asset.attachments &&
                                asset.attachments.length > 0 && (
                                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                                        <h3 className="text-lg font-semibold text-slate-900 mb-4">
                                            Attachments
                                        </h3>
                                        <div className="space-y-2">
                                            {asset.attachments.map(
                                                (attachment, idx) => (
                                                    <a
                                                        key={idx}
                                                        href={
                                                            attachment.file_url
                                                        }
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-700"
                                                    >
                                                        <FileText size={16} />
                                                        <span className="flex-1 truncate">
                                                            {
                                                                attachment.file_name
                                                            }
                                                        </span>
                                                        <ExternalLink
                                                            size={14}
                                                            className="text-slate-400"
                                                        />
                                                    </a>
                                                )
                                            )}
                                        </div>
                                    </div>
                                )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Report Modal */}
            {asset && (
                <ReportModal
                    isOpen={showReportModal}
                    onClose={() => setShowReportModal(false)}
                    asset={
                        {
                            id: asset.id,
                            _id: asset.id || asset.asset_code,
                            feature_type: asset.feature_type,
                            feature_code: asset.feature_code,
                            geometry: asset.geometry,
                            created_at: asset.created_at,
                        } as ApiAsset
                    }
                />
            )}
        </div>
    );
};

export default AssetDetailPage;
