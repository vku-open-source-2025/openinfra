import React, { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "./ui/button";
import {
    MapPin,
    Activity,
    Calendar,
    Tag,
    X,
    ChevronUp,
    ChevronDown,
    MessageCircle,
} from "lucide-react";
import type { Asset } from "../types/asset";
import { getHealthScoreColor, getHealthScoreLabel } from "../utils/healthScore";
import { format, formatDistanceToNow } from "date-fns";
import { vi } from "date-fns/locale";

interface AssetInfoPanelProps {
    asset: Asset | null;
    isOpen: boolean;
    onClose: () => void;
    onViewDetails?: (assetId: string) => void;
    onAddToChat?: (asset: Asset) => void;
    isLoading?: boolean;
}

const AssetInfoPanel: React.FC<AssetInfoPanelProps> = ({
    asset,
    isOpen,
    onClose,
    onViewDetails,
    onAddToChat,
    isLoading = false,
}) => {
    const navigate = useNavigate();
    const [isCollapsed, setIsCollapsed] = useState(false);

    if (!isOpen || !asset) return null;

    const healthScore = asset.lifecycle?.health_score ?? 0;
    const healthColor = getHealthScoreColor(healthScore);
    const healthLabel = getHealthScoreLabel(healthScore);
    const status = asset.status || "active";
    const lastMaintenance = asset.lifecycle?.last_maintenance_date;

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case "active":
            case "operational":
                return "bg-green-100 text-green-700";
            case "maintenance":
            case "under_repair":
                return "bg-yellow-100 text-yellow-700";
            case "inactive":
            case "damaged":
                return "bg-red-100 text-red-700";
            case "decommissioned":
                return "bg-slate-100 text-slate-700";
            default:
                return "bg-blue-100 text-blue-700";
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status.toLowerCase()) {
            case "active":
            case "operational":
                return "Đang hoạt động";
            case "maintenance":
            case "under_repair":
                return "Đang bảo trì";
            case "inactive":
            case "damaged":
                return "Ngưng hoạt động";
            case "decommissioned":
                return "Ngừng sử dụng";
            default:
                return "Chưa xác định";
        }
    };

    const getHealthScoreBarColor = () => {
        switch (healthColor) {
            case "green":
                return "bg-green-500";
            case "yellow":
                return "bg-yellow-500";
            case "orange":
                return "bg-orange-500";
            case "red":
                return "bg-red-500";
            default:
                return "bg-slate-500";
        }
    };

    const handleViewDetails = () => {
        const assetId =
            (asset as Asset & { id?: string; _id?: string }).id ||
            (asset as Asset & { id?: string; _id?: string })._id ||
            "";
        if (onViewDetails && assetId) {
            onViewDetails(assetId);
        } else if (assetId) {
            navigate({ to: "/admin/assets/$id", params: { id: assetId } });
        }
    };

    const formatAddress = () => {
        const { location } = asset;
        if (!location) {
            if (
                asset.geometry?.type === "Point" &&
                Array.isArray(asset.geometry.coordinates)
            ) {
                const [lng, lat] = asset.geometry.coordinates as number[];
                return `Vĩ độ: ${lat.toFixed(6)}, Kinh độ: ${lng.toFixed(6)}`;
            }
            return "Chưa có thông tin vị trí";
        }

        const parts = [
            location.address,
            location.ward,
            location.district,
            location.city,
        ].filter(Boolean);

        return parts.length > 0 ? parts.join(", ") : "Chưa có thông tin vị trí";
    };

    return (
        <div
            className={`absolute top-4 right-4 z-1000 w-full max-w-sm bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden flex flex-col transition-all duration-300 ${
                isCollapsed ? "max-h-14" : "max-h-[calc(100vh-8rem)]"
            }`}
        >
            {/* Header */}
            <div
                className="p-6 border-b border-slate-100 bg-slate-50 cursor-pointer hover:bg-slate-100 transition-colors"
                onClick={() => {
                    if (isCollapsed) {
                        setIsCollapsed(false);
                    }
                }}
            >
                <div className="flex items-start justify-between gap-3 mb-1">
                    <div className="flex-1 min-w-0">
                        {isLoading && (
                            <div className="mb-2 text-xs text-slate-500">
                                Đang tải chi tiết tài sản...
                            </div>
                        )}
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase tracking-wide">
                                {asset.feature_code || "N/A"}
                            </span>
                            <span
                                className={`px-2 py-1 text-xs font-semibold rounded uppercase tracking-wide ${getStatusColor(
                                    status
                                )}`}
                            >
                                {getStatusLabel(status)}
                            </span>
                        </div>
                        <h3 className="text-xl font-bold text-slate-900 truncate">
                            {(asset as Asset & { name?: string }).name ||
                                asset.feature_type ||
                                "Tài sản"}
                        </h3>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsCollapsed(!isCollapsed);
                            }}
                            className="p-1 hover:bg-slate-200 rounded transition-colors"
                            title={isCollapsed ? "Mở rộng" : "Thu gọn"}
                        >
                            {isCollapsed ? (
                                <ChevronDown size={18} />
                            ) : (
                                <ChevronUp size={18} />
                            )}
                        </button>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onClose();
                            }}
                            className="p-1 hover:bg-slate-200 rounded transition-colors"
                            title="Đóng"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Content */}
            {!isCollapsed && (
                <div className="flex-1 overflow-y-auto p-6">
                    <div className="space-y-4">
                        {/* Location - Always show */}
                        <div className="flex items-start gap-3">
                            <div className="p-2 bg-slate-100 rounded-lg shrink-0">
                                <MapPin className="h-5 w-5 text-slate-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                    Vị trí
                                </p>
                                <p className="text-sm text-slate-900 font-medium">
                                    {formatAddress()}
                                </p>
                            </div>
                        </div>

                        {/* Health Score */}
                        {healthScore > 0 && (
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-slate-100 rounded-lg shrink-0">
                                    <Activity className="h-5 w-5 text-slate-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between mb-2">
                                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                            Điểm sức khỏe
                                        </p>
                                        <span
                                            className={`text-sm font-bold ${
                                                healthColor === "green"
                                                    ? "text-green-600"
                                                    : healthColor === "yellow"
                                                    ? "text-yellow-600"
                                                    : healthColor === "orange"
                                                    ? "text-orange-600"
                                                    : "text-red-600"
                                            }`}
                                        >
                                            {healthScore}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-slate-200 rounded-full h-2.5 mb-1">
                                        <div
                                            className={`h-2.5 rounded-full transition-all duration-300 ${getHealthScoreBarColor()}`}
                                            style={{ width: `${healthScore}%` }}
                                        />
                                    </div>
                                    <p className="text-xs text-slate-600">
                                        Trạng thái: {healthLabel}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Category */}
                        {asset.category && (
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-slate-100 rounded-lg shrink-0">
                                    <Tag className="h-5 w-5 text-slate-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                        Phân loại
                                    </p>
                                    <p className="text-sm text-slate-900 font-medium">
                                        {asset.category}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Last Maintenance */}
                        {lastMaintenance && (
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-slate-100 rounded-lg shrink-0">
                                    <Calendar className="h-5 w-5 text-slate-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                        Bảo trì gần nhất
                                    </p>
                                    <p className="text-sm text-slate-900 font-medium">
                                        {formatDistanceToNow(
                                            new Date(lastMaintenance),
                                            {
                                                addSuffix: true,
                                                locale: vi,
                                            }
                                        )}
                                    </p>
                                    <p className="text-xs text-slate-500 mt-0.5">
                                        {format(
                                            new Date(lastMaintenance),
                                            "dd/MM/yyyy"
                                        )}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Next Maintenance */}
                        {asset.lifecycle?.next_maintenance_date && (
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-slate-100 rounded-lg shrink-0">
                                    <Calendar className="h-5 w-5 text-slate-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                        Lịch bảo trì kế tiếp
                                    </p>
                                    <p className="text-sm text-slate-900 font-medium">
                                        {format(
                                            new Date(
                                                asset.lifecycle.next_maintenance_date
                                            ),
                                            "dd/MM/yyyy"
                                        )}
                                    </p>
                                    {asset.lifecycle.maintenance_overdue && (
                                        <p className="text-xs text-red-600 font-medium mt-0.5">
                                            Quá hạn
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            {!isCollapsed && (
                <div className="p-4 border-t border-slate-100 bg-slate-50 flex gap-2">
                    {onAddToChat && (
                        <Button
                            variant="outline"
                            onClick={() => onAddToChat(asset)}
                            className="flex-1 flex items-center justify-center gap-2"
                        >
                            <MessageCircle size={16} />
                            Thêm vào hội thoại
                        </Button>
                    )}
                    <Button
                        onClick={handleViewDetails}
                        className={`${onAddToChat ? 'flex-1' : 'w-full'} bg-blue-600 hover:bg-blue-700 text-white`}
                    >
                        Xem chi tiết
                    </Button>
                </div>
            )}
        </div>
    );
};

export default AssetInfoPanel;
