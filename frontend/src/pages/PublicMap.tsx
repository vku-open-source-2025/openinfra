import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearch, useNavigate } from "@tanstack/react-router";
import { getAssets, getAssetId, type Asset } from "../api";
import MapComponent from "../components/Map";
import MaintenanceLogList from "../components/MaintenanceLog";
import { useIoT } from "../hooks/useIoT";
import {
    AlertTriangle,
    Clock3,
    ExternalLink,
    Layers,
    MapPin,
    MessageCircle,
    X,
} from "lucide-react";
import Header from "../components/Header";
import QRCodeModal from "../components/QRCodeModal";
import NFCWriteModal from "../components/NFCWriteModal";
import ReportModal from "../components/ReportModal";
import IoTSensorChart from "../components/IoTSensorChart";
import { Button } from "@/components/ui/button";
import AIChatWidget from "../components/AIChatWidget";
import HazardMarkersLayer from "../components/HazardMarkersLayer";
import VndmsHazardLayer, { VndmsLegend } from "../components/VndmsHazardLayer";
import { useVndmsHazards } from "../hooks/useVndmsHazards";
import { hazardsApi } from "../api/hazards";
import type { Hazard } from "../types/hazard";
import { getHazardTimestampMs } from "../lib/recentHazards";
import L from "leaflet";

// Extended Asset type with status added by useIoT hook
type AssetWithStatus = Asset & {
    status?: "Online" | "Offline";
    lastPing?: string;
};

const RECENT_HAZARD_WINDOW_HOURS = 24;

const HAZARD_SEVERITY_LABEL: Record<string, string> = {
    low: "Thấp",
    medium: "Trung bình",
    high: "Cao",
    critical: "Nghiêm trọng",
};

const HAZARD_SEVERITY_BADGE: Record<string, string> = {
    low: "bg-green-100 text-green-700",
    medium: "bg-amber-100 text-amber-700",
    high: "bg-red-100 text-red-700",
    critical: "bg-purple-100 text-purple-700",
};

const HAZARD_EVENT_LABEL: Record<string, string> = {
    flood: "Lũ lụt",
    storm: "Bão",
    landslide: "Sạt lở",
    fire: "Cháy",
    earthquake: "Động đất",
    outage: "Mất điện",
    pollution: "Ô nhiễm",
    drought: "Hạn hán",
    traffic: "Giao thông",
    epidemic: "Dịch bệnh",
    infrastructure_failure: "Sự cố hạ tầng",
    other: "Khác",
};

const HAZARD_SOURCE_LABEL: Record<string, string> = {
    manual: "Nội bộ",
    iot: "IoT",
    vndms: "VNDMS",
    nchmf: "NCHMF",
    other: "Khác",
};

function formatHazardTime(hazard: Hazard): string {
    const timestampMs = getHazardTimestampMs(hazard);
    if (timestampMs === null) {
        return "Không rõ thời gian";
    }

    return new Date(timestampMs).toLocaleString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
    });
}

function formatHazardLocation(hazard: Hazard): string {
    const parts = [hazard.ward, hazard.district].filter(
        (part): part is string => typeof part === "string" && part.trim().length > 0
    );
    if (parts.length === 0) {
        return "Không rõ vị trí";
    }
    return parts.join(", ");
}

function canFocusHazardOnMap(hazard: Hazard): boolean {
    return (
        hazard.geometry?.type === "Point" &&
        Array.isArray(hazard.geometry.coordinates) &&
        hazard.geometry.coordinates.length >= 2 &&
        typeof hazard.geometry.coordinates[0] === "number" &&
        typeof hazard.geometry.coordinates[1] === "number"
    );
}

const PublicMap: React.FC = () => {
    const navigate = useNavigate();
    const searchParams = useSearch({ from: "/map" }) as { assetId?: string };
    const {
        data: initialAssets,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["assets"],
        queryFn: getAssets,
        staleTime: 5 * 60 * 1000, // 5 minutes - prevent refetch on navigation
        refetchOnWindowFocus: false,
    });

    const { assetsWithStatus, alerts } = useIoT(initialAssets);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [filteredAssets, setFilteredAssets] = useState<Asset[] | null>(null);
    const [routePoints] = useState<Asset[]>([]);
    const [showAssetInfoModal, setShowAssetInfoModal] = useState(false);

    const [showQRModal, setShowQRModal] = useState(false);
    const [showNFCModal, setShowNFCModal] = useState(false);
    const [showReportModal, setShowReportModal] = useState(false);
    const [openChatbot, setOpenChatbot] = useState(false);
    const [assetToAddToChat, setAssetToAddToChat] = useState<Asset | null>(null);

    // Hazard layer state — default on so citizens see alerts immediately
    const [showHazardLayer, setShowHazardLayer] = useState(true);
    const [leafletMap, setLeafletMap] = useState<L.Map | null>(null);
    const [focusedHazardId, setFocusedHazardId] = useState<string | null>(null);
    const [hazardFocusNonce, setHazardFocusNonce] = useState(0);
    // Our own stored hazards (e.g. manual / IoT-based)
    const { data: hazards = [] } = useQuery({
        queryKey: ["hazards", "active"],
        queryFn: () => hazardsApi.list({ is_active: true }),
        staleTime: 60 * 1000,
    });
    const {
        data: recentHazards = [],
        isLoading: isRecentHazardsLoading,
    } = useQuery({
        queryKey: ["hazards", "recent", RECENT_HAZARD_WINDOW_HOURS],
        queryFn: () => hazardsApi.listRecent({
            hours: RECENT_HAZARD_WINDOW_HOURS,
            is_active: true,
            limit: 200,
        }),
        staleTime: 60 * 1000,
        refetchInterval: 2 * 60 * 1000,
    });
    // Live VNDMS national-scale hazards (realtime weather + disaster)
    const { data: vndmsHazards = [] } = useVndmsHazards(true);

    // Use filtered assets if available, otherwise use live IoT assets
    const displayAssets = useMemo(() => {
        return filteredAssets || assetsWithStatus || [];
    }, [filteredAssets, assetsWithStatus]);

    // Sync URL param with selected asset - only on initial load or when assets are loaded
    const initialAssetIdRef = React.useRef(searchParams?.assetId);
    useEffect(() => {
        const assetId = initialAssetIdRef.current;
        if (assetId && displayAssets.length > 0 && !selectedAsset) {
            const asset = displayAssets.find((a) => getAssetId(a) === assetId);
            if (asset) {
                setSelectedAsset(asset);
                setShowAssetInfoModal(true);
            }
        }
    }, [displayAssets, selectedAsset]);

    const handleAssetSelect = (asset: Asset | null) => {
        setSelectedAsset(asset);
        setShowAssetInfoModal(asset !== null);
        // Close chat panel when opening asset details
        if (asset !== null) {
            setOpenChatbot(false);
            setAssetToAddToChat(null);
        }
        // Update URL without causing re-render
        const newUrl = asset
            ? `${window.location.pathname}?assetId=${getAssetId(asset)}`
            : window.location.pathname;
        window.history.replaceState({}, "", newUrl);
    };

    const handleCloseAssetInfoModal = () => {
        setShowAssetInfoModal(false);
        setSelectedAsset(null);
        // Update URL without causing re-render
        window.history.replaceState({}, "", window.location.pathname);
    };

    const handleFocusHazard = (hazard: Hazard) => {
        if (!leafletMap || !canFocusHazardOnMap(hazard)) {
            return;
        }

        const [lng, lat] = hazard.geometry.coordinates as number[];
        setShowHazardLayer(true);
        setFocusedHazardId(hazard.id);
        setHazardFocusNonce((value) => value + 1);
        leafletMap.flyTo([lat, lng], Math.max(leafletMap.getZoom(), 13), {
            animate: true,
            duration: 1.1,
        });
    };

    if (isLoading)
        return (
            <div className="flex h-screen items-center justify-center bg-slate-50">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-500 font-medium">
                        Đang tải tài nguyên hệ thống...
                    </p>
                </div>
            </div>
        );

    if (error)
        return (
            <div className="p-8 text-center text-red-500">
                Lỗi khi tải danh sách tài sản
            </div>
        );

    return (
        <div className="flex flex-col h-screen bg-slate-50 font-sans text-slate-900">
            <Header />

            <main className="flex-1 flex flex-col relative pt-20 z-0">
                {/* Alert Feed Overlay */}
                {alerts.length > 0 && (
                    <div className="absolute top-24 right-8 z-50 w-80 pointer-events-none">
                        {alerts.map((alert, idx) => (
                            <div
                                key={idx}
                                className="bg-red-50 border-l-4 border-red-500 p-3 mb-2 shadow-lg rounded-r animate-in slide-in-from-right fade-in duration-300 pointer-events-auto flex items-start gap-3"
                            >
                                <AlertTriangle
                                    className="text-red-500 shrink-0"
                                    size={18}
                                />
                                <p className="text-xs font-medium text-red-800">
                                    {alert}
                                </p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Fullscreen Map */}
                <div className="flex-1 w-full relative overflow-hidden">
                    <MapComponent
                        assets={displayAssets}
                        onAssetSelect={handleAssetSelect}
                        onFilterByShape={setFilteredAssets}
                        routePoints={routePoints}
                        selectedAsset={selectedAsset}
                        className="h-full w-full"
                        enableGeoSearches={true}
                        onMapReady={setLeafletMap}
                    />
                    {/* Hazard layer overlay */}
                    {showHazardLayer && leafletMap && hazards.length > 0 && (
                        <HazardMarkersLayer
                            map={leafletMap}
                            hazards={hazards}
                            focusedHazardId={focusedHazardId}
                            focusNonce={hazardFocusNonce}
                        />
                    )}
                    {showHazardLayer && leafletMap && vndmsHazards.length > 0 && (
                        <VndmsHazardLayer map={leafletMap} hazards={vndmsHazards} />
                    )}
                    {/* Hazard legend — top-right stack */}
                    {showHazardLayer && (
                        <div className="absolute top-24 right-4 z-[1000]">
                            <VndmsLegend />
                        </div>
                    )}
                    {/* Hazard layer toggle button — top-right, prominent */}
                    <button
                        onClick={() => setShowHazardLayer((v) => !v)}
                        title={showHazardLayer ? "Ẩn lớp thiên tai" : "Hiện lớp thiên tai"}
                        className={`absolute top-24 right-4 z-[1001] flex items-center gap-2 px-3 py-2 rounded-lg shadow-lg border text-sm font-medium transition-colors ${
                            showHazardLayer
                                ? "bg-red-600 border-red-700 text-white hover:bg-red-700"
                                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                        }`}
                        style={{ transform: showHazardLayer ? "translateY(-44px)" : undefined }}
                    >
                        <Layers size={16} />
                        <span>Thiên tai (24h)</span>
                        {(hazards.length + vndmsHazards.length) > 0 && (
                            <span
                                className={`text-xs font-bold rounded-full px-1.5 py-0.5 leading-none ${
                                    showHazardLayer
                                        ? "bg-white text-red-600"
                                        : "bg-red-600 text-white"
                                }`}
                            >
                                {hazards.length + vndmsHazards.length}
                            </span>
                        )}
                    </button>

                    {/* Recent hazards bottom panel */}
                    <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[1000] px-3 pb-3 sm:px-4 sm:pb-4">
                        <section className="pointer-events-auto rounded-xl border border-slate-200 bg-white/95 shadow-xl backdrop-blur supports-[backdrop-filter]:bg-white/80">
                            <div className="flex items-center justify-between gap-2 border-b border-slate-200 px-3 py-2 sm:px-4">
                                <div className="flex items-center gap-2">
                                    <AlertTriangle size={14} className="text-amber-600" />
                                    <div>
                                        <p className="text-sm font-semibold text-slate-800">
                                            Thiên tai 24h gần nhất
                                        </p>
                                        <p className="text-xs text-slate-500">
                                            {recentHazards.length} sự kiện
                                        </p>
                                    </div>
                                </div>
                                {isRecentHazardsLoading && (
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
                                )}
                            </div>

                            <div className="px-2 pb-2 pt-2 sm:px-3">
                                {isRecentHazardsLoading ? (
                                    <p className="px-2 py-3 text-xs text-slate-500">
                                        Đang tải dữ liệu thiên tai...
                                    </p>
                                ) : recentHazards.length === 0 ? (
                                    <p className="px-2 py-3 text-xs text-slate-500">
                                        Không có sự kiện thiên tai nào trong 24 giờ qua.
                                    </p>
                                ) : (
                                    <ul className="flex gap-2 overflow-x-auto pb-1">
                                        {recentHazards.map((hazard) => {
                                            const severityClass =
                                                HAZARD_SEVERITY_BADGE[
                                                    hazard.severity
                                                ] ?? "bg-slate-100 text-slate-700";
                                            const severityLabel =
                                                HAZARD_SEVERITY_LABEL[
                                                    hazard.severity
                                                ] ?? hazard.severity;
                                            const typeLabel =
                                                HAZARD_EVENT_LABEL[
                                                    hazard.event_type
                                                ] ?? hazard.event_type;
                                            const sourceLabel =
                                                HAZARD_SOURCE_LABEL[
                                                    hazard.source
                                                ] ?? hazard.source;
                                            const canFocus =
                                                canFocusHazardOnMap(hazard);
                                            const isFocused =
                                                focusedHazardId === hazard.id;

                                            return (
                                                <li
                                                    key={hazard.id}
                                                    className="max-w-[280px] min-w-[220px] sm:min-w-[250px]"
                                                >
                                                    <button
                                                        type="button"
                                                        disabled={!canFocus}
                                                        onClick={() =>
                                                            handleFocusHazard(
                                                                hazard
                                                            )
                                                        }
                                                        className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                                                            isFocused
                                                                ? "border-blue-400 bg-blue-50"
                                                                : "border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/40"
                                                        } ${
                                                            canFocus
                                                                ? "cursor-pointer"
                                                                : "cursor-not-allowed opacity-70"
                                                        }`}
                                                    >
                                                        <div className="flex items-center justify-between gap-2">
                                                            <span
                                                                className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-bold ${severityClass}`}
                                                            >
                                                                {severityLabel}
                                                            </span>
                                                            <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                                                                <Clock3
                                                                    size={11}
                                                                />
                                                                {formatHazardTime(
                                                                    hazard
                                                                )}
                                                            </span>
                                                        </div>
                                                        <p className="mt-1 truncate text-sm font-semibold text-slate-900">
                                                            {hazard.title ||
                                                                "Cảnh báo thiên tai"}
                                                        </p>
                                                        <p className="text-xs text-slate-500">
                                                            {typeLabel}
                                                        </p>
                                                        <p className="mt-1 truncate text-xs text-slate-600">
                                                            {formatHazardLocation(
                                                                hazard
                                                            )}
                                                            {" - "}
                                                            {sourceLabel}
                                                        </p>
                                                        <p
                                                            className={`mt-1 inline-flex items-center gap-1 text-[11px] font-medium ${
                                                                canFocus
                                                                    ? "text-blue-600"
                                                                    : "text-slate-400"
                                                            }`}
                                                        >
                                                            <MapPin
                                                                size={11}
                                                            />
                                                            {canFocus
                                                                ? "Xem vị trí trên bản đồ"
                                                                : "Chưa có tọa độ điểm"}
                                                        </p>
                                                    </button>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                )}
                            </div>
                        </section>
                    </div>
                </div>

                {/* Asset Info Modal */}
                {showAssetInfoModal && selectedAsset && (
                    <div className="fixed top-20 right-0 bottom-0 z-[1000] flex items-start justify-end p-4">
                        <div className="bg-white rounded-l-xl shadow-xl w-full max-w-2xl h-full overflow-hidden flex flex-col animate-in slide-in-from-right fade-in duration-200">
                            {/* Modal Header */}
                            <div className="p-6 border-b border-slate-100 bg-slate-50 flex items-start justify-between gap-3 shrink-0">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase tracking-wide">
                                            {selectedAsset.feature_code}
                                        </span>
                                        <span className="text-xs text-slate-400">
                                            ID:{" "}
                                            {getAssetId(selectedAsset).slice(
                                                -6
                                            )}
                                        </span>
                                        {(selectedAsset as AssetWithStatus)
                                            .status && (
                                            <span
                                                className={`px-2 py-1 text-xs font-bold rounded uppercase tracking-wide ${
                                                    (
                                                        selectedAsset as AssetWithStatus
                                                    ).status === "Online"
                                                        ? "bg-green-100 text-green-700"
                                                        : "bg-red-100 text-red-700"
                                                }`}
                                            >
                                                {(
                                                    selectedAsset as AssetWithStatus
                                                ).status === "Online"
                                                    ? "Trực tuyến"
                                                    : "Ngoại tuyến"}
                                            </span>
                                        )}
                                    </div>
                                    <h3 className="text-xl font-bold text-slate-900">
                                        {selectedAsset.feature_type}
                                    </h3>
                                </div>
                                <button
                                    onClick={handleCloseAssetInfoModal}
                                    className="p-1 hover:bg-slate-200 rounded transition-colors shrink-0"
                                    title="Đóng"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Modal Content */}
                            <div className="flex-1 overflow-y-auto p-6">
                                <div className="space-y-6">
                                    {/* Location */}
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                            Vị trí
                                        </h4>
                                        <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                            {selectedAsset.geometry.type ===
                                                "Point" &&
                                            Array.isArray(
                                                selectedAsset.geometry
                                                    .coordinates
                                            ) ? (
                                                <div className="grid grid-cols-2 gap-4 text-sm">
                                                    <div>
                                                        <p className="text-slate-500 text-xs">
                                                            Vĩ độ
                                                        </p>
                                                        <p className="font-mono font-medium">
                                                            {(
                                                                selectedAsset
                                                                    .geometry
                                                                    .coordinates[1] as number
                                                            ).toFixed(6)}
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-slate-500 text-xs">
                                                            Kinh độ
                                                        </p>
                                                        <p className="font-mono font-medium">
                                                            {(
                                                                selectedAsset
                                                                    .geometry
                                                                    .coordinates[0] as number
                                                            ).toFixed(6)}
                                                        </p>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="text-sm">
                                                    <p className="text-slate-500 text-xs mb-1">
                                                        Loại hình học
                                                    </p>
                                                    <p className="font-mono font-medium mb-2">
                                                        {
                                                            selectedAsset
                                                                .geometry.type
                                                        }
                                                    </p>
                                                    <p className="text-slate-500 text-xs mb-1">
                                                        Chi tiết
                                                    </p>
                                                    <p className="font-mono font-medium">
                                                        {selectedAsset.geometry
                                                            .type ===
                                                        "LineString"
                                                            ? `${selectedAsset.geometry.coordinates.length} điểm`
                                                            : "Hình học phức tạp"}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Maintenance History */}
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                            Lịch sử bảo trì
                                        </h4>
                                        <MaintenanceLogList
                                            assetId={getAssetId(selectedAsset)}
                                        />
                                    </div>

                                    {/* IoT Sensor Data */}
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                            Dữ liệu cảm biến IoT
                                        </h4>
                                        <IoTSensorChart
                                            assetId={getAssetId(selectedAsset)}
                                            assetName={
                                                selectedAsset.feature_type
                                            }
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Modal Actions */}
                            <div className="px-8 py-4 border-t border-slate-100 bg-slate-50 flex gap-2 shrink-0 justify-end">
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        setAssetToAddToChat(selectedAsset);
                                        setOpenChatbot(true);
                                        handleCloseAssetInfoModal();
                                    }}
                                    className="flex flex-row items-center gap-2"
                                >
                                    <MessageCircle size={16} />
                                    Thêm vào hội thoại
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        const assetId =
                                            getAssetId(selectedAsset);
                                        navigate({
                                            to: "/asset/$id",
                                            params: { id: assetId },
                                        });
                                    }}
                                    className="flex flex-row items-center gap-2"
                                >
                                    <ExternalLink size={16} />
                                    Xem chi tiết
                                </Button>
                                <Button
                                    className="flex flex-row items-center gap-2"
                                    variant="destructive"
                                    onClick={() => setShowReportModal(true)}
                                >
                                    <AlertTriangle size={16} />
                                    Báo cáo
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                <QRCodeModal
                    isOpen={showQRModal}
                    onClose={() => setShowQRModal(false)}
                    asset={selectedAsset}
                />

                <NFCWriteModal
                    isOpen={showNFCModal}
                    onClose={() => setShowNFCModal(false)}
                    asset={selectedAsset}
                />

                <ReportModal
                    isOpen={showReportModal}
                    onClose={() => setShowReportModal(false)}
                    asset={selectedAsset}
                />

                {/* AI Chatbot Widget */}
                <AIChatWidget 
                    openChat={openChatbot}
                    onOpenChange={(isOpen) => {
                        setOpenChatbot(isOpen);
                        if (isOpen) {
                            // Close asset details panel when opening chat
                            setShowAssetInfoModal(false);
                            setSelectedAsset(null);
                            window.history.replaceState({}, "", window.location.pathname);
                        } else {
                            // Reset asset to add when closing
                            setAssetToAddToChat(null);
                        }
                    }}
                    addAssetToContext={assetToAddToChat}
                />
            </main>
        </div>
    );
};

export default PublicMap;
