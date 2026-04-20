import React, { useState, useCallback } from "react";
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
    AlertTriangle,
    RefreshCw,
    MapPin,
    Clock,
    ShieldAlert,
    Megaphone,
    X,
    Phone,
} from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchTileConfig } from "../lib/tileConfig";
import VndmsHazardLayer, {
    useVndmsHazards,
    VndmsLegend,
    type VndmsHazard,
} from "../components/VndmsHazardLayer";
import HazardMarkersLayer from "../components/HazardMarkersLayer";
import { hazardsApi } from "../api/hazards";
import IncidentReportForm from "../components/IncidentReportForm";
import type { Hazard } from "../types/hazard";

// ── Visual maps ──────────────────────────────────────────────────────────────

const TYPE_LABEL_VI: Record<string, string> = {
    water_level: "Mực nước",
    warning_rain: "Cảnh báo mưa",
    warning_wind: "Cảnh báo gió",
    warning_earthquake: "Động đất",
    warning_flood: "Lũ lụt",
};

const TYPE_EMOJI: Record<string, string> = {
    water_level: "💧",
    warning_rain: "🌧️",
    warning_wind: "💨",
    warning_earthquake: "🌍",
    warning_flood: "🌊",
};

const SEVERITY_BG: Record<string, string> = {
    low: "bg-green-100 text-green-800",
    medium: "bg-yellow-100 text-yellow-800",
    high: "bg-red-100 text-red-800",
};

const SEVERITY_LABEL: Record<string, string> = {
    low: "Thấp",
    medium: "Trung bình",
    high: "Cao",
};

// ── Vndms hazard card ────────────────────────────────────────────────────────

const VndmsCard: React.FC<{
    hazard: VndmsHazard;
    onLocate: (h: VndmsHazard) => void;
}> = ({ hazard, onLocate }) => (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
        <div className="p-3">
            <div className="flex items-start gap-2.5">
                <span className="text-xl flex-shrink-0 mt-0.5">
                    {TYPE_EMOJI[hazard.warning_type] ?? "⚠️"}
                </span>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap mb-1">
                        <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SEVERITY_BG[hazard.severity] ?? "bg-slate-100 text-slate-700"}`}
                        >
                            {SEVERITY_LABEL[hazard.severity] ?? hazard.severity}
                        </span>
                        <span className="text-[10px] text-slate-500">
                            {TYPE_LABEL_VI[hazard.warning_type] ?? hazard.warning_type}
                        </span>
                    </div>
                    <h3 className="font-semibold text-slate-900 text-sm leading-snug truncate">
                        {hazard.label || "(Không tên)"}
                    </h3>
                    {hazard.value && (
                        <p className="text-xs text-slate-600 mt-0.5">
                            Giá trị: <span className="font-medium">{hazard.value}</span>
                        </p>
                    )}
                </div>
                <button
                    onClick={() => onLocate(hazard)}
                    title="Xem trên bản đồ"
                    className="flex-shrink-0 p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                >
                    <MapPin size={14} />
                </button>
            </div>
        </div>
    </div>
);

// ── Stored hazard card ───────────────────────────────────────────────────────

const StoredHazardCard: React.FC<{
    hazard: Hazard;
    onLocate: (h: Hazard) => void;
}> = ({ hazard, onLocate }) => (
    <div
        className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden border-l-4"
        style={{
            borderLeftColor:
                hazard.severity === "critical"
                    ? "#7c3aed"
                    : hazard.severity === "high"
                    ? "#ef4444"
                    : hazard.severity === "medium"
                    ? "#f59e0b"
                    : "#22c55e",
        }}
    >
        <div className="p-3 flex items-start gap-2.5">
            <span className="text-xl flex-shrink-0 mt-0.5">⚠️</span>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap mb-1">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                        Nội bộ
                    </span>
                    <span className="text-[10px] text-slate-500">
                        {hazard.event_type}
                    </span>
                </div>
                <h3 className="font-semibold text-slate-900 text-sm leading-snug">
                    {hazard.title}
                </h3>
                {hazard.district && (
                    <p className="text-xs text-slate-500 mt-0.5">
                        📍 {hazard.district}
                    </p>
                )}
            </div>
            <button
                onClick={() => onLocate(hazard)}
                className="flex-shrink-0 p-1.5 text-blue-600 hover:bg-blue-50 rounded"
            >
                <MapPin size={14} />
            </button>
        </div>
    </div>
);

// ── Helpers ──────────────────────────────────────────────────────────────────

function timeAgo(ms: number): string {
    const diff = Date.now() - ms;
    const m = Math.floor(diff / 60000);
    if (m < 1) return "Vừa xong";
    if (m < 60) return `${m} phút trước`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h} giờ trước`;
    return `${Math.floor(h / 24)} ngày trước`;
}

const VIETNAM_CENTER: [number, number] = [16.0, 107.0];

// ── Main page ────────────────────────────────────────────────────────────────

const DisasterMap: React.FC = () => {
    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const mapRef = React.useRef<L.Map | null>(null);
    const [leafletMap, setLeafletMap] = useState<L.Map | null>(null);

    const [filterSeverity, setFilterSeverity] = useState<string>("all");
    const [filterType, setFilterType] = useState<string>("all");
    const [showReportModal, setShowReportModal] = useState(false);
    const [isPickingOnMap, setIsPickingOnMap] = useState(false);
    const [pickedCoords, setPickedCoords] = useState<
        { latitude: number; longitude: number } | undefined
    >(undefined);
    const pickedMarkerRef = React.useRef<L.Marker | null>(null);

    const {
        data: vndmsHazards = [],
        isLoading,
        refetch,
        isFetching,
        dataUpdatedAt,
    } = useVndmsHazards(true);

    const { data: storedHazards = [] } = useQuery({
        queryKey: ["hazards", "active-public"],
        queryFn: () => hazardsApi.list({ is_active: true, limit: 200 }),
        staleTime: 60_000,
        refetchInterval: 5 * 60_000,
    });

    // Initialize the map (centered on Vietnam, zoom out so user sees national-scale data)
    React.useEffect(() => {
        if (!containerRef.current || mapRef.current) return;
        const map = L.map(containerRef.current, {
            center: VIETNAM_CENTER,
            zoom: 6,
            maxZoom: 19,
            scrollWheelZoom: true,
        });
        fetchTileConfig().then((cfg) => {
            if (!mapRef.current) return;
            L.tileLayer(cfg.tileUrl, {
                attribution: cfg.attribution,
                maxZoom: cfg.maxZoom,
                ...(cfg.maxNativeZoom ? { maxNativeZoom: cfg.maxNativeZoom } : {}),
            }).addTo(mapRef.current);
        });
        mapRef.current = map;
        setLeafletMap(map);
        return () => {
            map.remove();
            mapRef.current = null;
            setLeafletMap(null);
        };
    }, []);

    // ── Filtering ─────────────────────────────────────────────────────────────
    const filteredVndms = vndmsHazards
        .filter((h) => filterSeverity === "all" || h.severity === filterSeverity)
        .filter((h) => filterType === "all" || h.warning_type === filterType);

    const availableTypes = Array.from(
        new Set(vndmsHazards.map((h) => h.warning_type))
    );

    const handleLocateVndms = useCallback(
        (h: VndmsHazard) => {
            if (!leafletMap) return;
            leafletMap.flyTo([h.lat, h.lon], 11, {
                animate: true,
                duration: 1.2,
            });
        },
        [leafletMap]
    );

    const handleLocateStored = useCallback(
        (h: Hazard) => {
            if (!leafletMap || !h.geometry?.coordinates) return;
            if (h.geometry.type === "Point") {
                const [lng, lat] = h.geometry.coordinates as number[];
                leafletMap.flyTo([lat, lng], 14, { animate: true, duration: 1.2 });
            }
        },
        [leafletMap]
    );

    const criticalCount = vndmsHazards.filter((h) => h.severity === "high").length;
    const totalCount = filteredVndms.length + storedHazards.length;

    // ── Pick-on-map handlers ─────────────────────────────────────────────────
    const placePickedMarker = useCallback(
        (lat: number, lng: number) => {
            if (!leafletMap) return;
            if (pickedMarkerRef.current) {
                pickedMarkerRef.current.setLatLng([lat, lng]);
            } else {
                const icon = L.divIcon({
                    className: "",
                    html: `<div style="
                        width:32px;height:32px;border-radius:50% 50% 50% 0;
                        background:#f59e0b;
                        transform:rotate(-45deg);
                        border:3px solid white;
                        box-shadow:0 2px 6px rgba(0,0,0,0.4);
                        display:flex;align-items:center;justify-content:center;
                        ">
                          <span style="transform:rotate(45deg);font-size:14px">📍</span>
                        </div>`,
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                });
                pickedMarkerRef.current = L.marker([lat, lng], { icon }).addTo(
                    leafletMap
                );
            }
        },
        [leafletMap]
    );

    const startPickOnMap = useCallback(() => {
        setIsPickingOnMap(true);
        setShowReportModal(false); // hide modal so user can see/click the map
    }, []);

    // Map click listener — only active while picking
    React.useEffect(() => {
        if (!leafletMap || !isPickingOnMap) return;

        // Change cursor to crosshair
        const container = leafletMap.getContainer();
        const prevCursor = container.style.cursor;
        container.style.cursor = "crosshair";

        const handler = (e: L.LeafletMouseEvent) => {
            const { lat, lng } = e.latlng;
            setPickedCoords({ latitude: lat, longitude: lng });
            placePickedMarker(lat, lng);
            setIsPickingOnMap(false);
            setShowReportModal(true); // reopen the modal
        };
        leafletMap.on("click", handler);
        return () => {
            leafletMap.off("click", handler);
            container.style.cursor = prevCursor;
        };
    }, [leafletMap, isPickingOnMap, placePickedMarker]);

    // Cleanup picked marker when modal closed without submitting
    const handleCloseReportModal = useCallback(() => {
        setShowReportModal(false);
        setIsPickingOnMap(false);
        if (pickedMarkerRef.current && leafletMap) {
            leafletMap.removeLayer(pickedMarkerRef.current);
            pickedMarkerRef.current = null;
        }
        setPickedCoords(undefined);
    }, [leafletMap]);

    return (
        <div className="flex flex-col h-screen bg-slate-50 font-sans text-slate-900">
            {/* ── Header ── */}
            <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3 z-50 relative shadow-sm">
                <Link to="/" className="hidden sm:block">
                    <h1 className="text-lg font-bold bg-gradient-to-b from-[#4FACFE] from-21% to-[#00F2FE] bg-clip-text text-transparent">
                        OpenInfra
                    </h1>
                </Link>
                <div className="hidden sm:block w-px h-6 bg-slate-200" />

                <div className="flex items-center gap-2">
                    <ShieldAlert className="text-red-600" size={22} />
                    <div>
                        <h2 className="font-bold text-slate-900 text-sm leading-tight">
                            Bản đồ cảnh báo thiên tai
                        </h2>
                        <p className="text-xs text-slate-500 hidden sm:block">
                            Dành cho người dân — dữ liệu VNDMS realtime
                        </p>
                    </div>
                </div>

                <div className="ml-auto flex items-center gap-2">
                    {criticalCount > 0 && (
                        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-red-50 border border-red-200 rounded-full text-red-700 text-xs font-bold animate-pulse">
                            <AlertTriangle size={13} />
                            {criticalCount} cảnh báo cao
                        </div>
                    )}
                    <a
                        href="tel:114"
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors"
                        title="Gọi cứu hỏa khẩn cấp"
                    >
                        <Phone size={14} />
                        <span className="hidden sm:inline">114</span>
                    </a>
                    <button
                        onClick={() => setShowReportModal(true)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 text-white text-sm font-semibold hover:bg-amber-600 transition-colors"
                        title="Báo sự cố"
                    >
                        <Megaphone size={14} />
                        <span className="hidden sm:inline">Báo sự cố</span>
                    </button>
                    <button
                        onClick={() => refetch()}
                        disabled={isFetching}
                        title="Làm mới"
                        className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw
                            size={16}
                            className={isFetching ? "animate-spin" : ""}
                        />
                    </button>
                </div>
            </header>

            {/* ── Body ── */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <aside className="w-80 flex flex-col border-r border-slate-200 bg-white overflow-hidden shrink-0">
                    {/* Filter bar */}
                    <div className="p-3 border-b border-slate-100 space-y-2 shrink-0">
                        <select
                            value={filterSeverity}
                            onChange={(e) => setFilterSeverity(e.target.value)}
                            className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-red-400"
                        >
                            <option value="all">Tất cả mức độ</option>
                            <option value="high">🔴 Cao</option>
                            <option value="medium">🟡 Trung bình</option>
                            <option value="low">🟢 Thấp</option>
                        </select>
                        <select
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                            className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-red-400"
                        >
                            <option value="all">Tất cả loại</option>
                            {availableTypes.map((t) => (
                                <option key={t} value={t}>
                                    {TYPE_EMOJI[t]} {TYPE_LABEL_VI[t] ?? t}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Summary */}
                    <div className="px-3 py-2 border-b border-slate-100 text-xs text-slate-500 shrink-0 flex items-center gap-1">
                        <Clock size={11} />
                        {isLoading ? (
                            "Đang tải..."
                        ) : (
                            <>
                                <span className="font-semibold text-slate-700">
                                    {totalCount}
                                </span>
                                <span>điểm cảnh báo</span>
                                {dataUpdatedAt > 0 && (
                                    <span className="ml-auto text-slate-400">
                                        {timeAgo(dataUpdatedAt)}
                                    </span>
                                )}
                            </>
                        )}
                    </div>

                    {/* List */}
                    <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
                        {isLoading ? (
                            <div className="flex justify-center py-12">
                                <div className="w-8 h-8 border-4 border-red-500 border-t-transparent rounded-full animate-spin" />
                            </div>
                        ) : totalCount === 0 ? (
                            <div className="text-center py-12 text-slate-400">
                                <ShieldAlert
                                    size={32}
                                    className="mx-auto mb-2 opacity-30"
                                />
                                <p className="text-sm">Không có cảnh báo nào</p>
                                <p className="text-xs mt-1">Khu vực hiện tại an toàn ✓</p>
                            </div>
                        ) : (
                            <>
                                {storedHazards.map((h) => (
                                    <StoredHazardCard
                                        key={h.id}
                                        hazard={h}
                                        onLocate={handleLocateStored}
                                    />
                                ))}
                                {filteredVndms.map((h) => (
                                    <VndmsCard
                                        key={h.id}
                                        hazard={h}
                                        onLocate={handleLocateVndms}
                                    />
                                ))}
                            </>
                        )}
                    </div>
                </aside>

                {/* Map */}
                <div className="flex-1 relative overflow-hidden">
                    <div ref={containerRef} className="w-full h-full" />
                    {leafletMap && filteredVndms.length > 0 && (
                        <VndmsHazardLayer
                            map={leafletMap}
                            hazards={filteredVndms}
                        />
                    )}
                    {leafletMap && storedHazards.length > 0 && (
                        <HazardMarkersLayer
                            map={leafletMap}
                            hazards={storedHazards}
                        />
                    )}

                    {/* Legend */}
                    <div className="absolute bottom-4 left-4 z-[1000]">
                        <VndmsLegend />
                    </div>
                </div>
            </div>

            {/* ── Pick-on-map banner ── */}
            {isPickingOnMap && (
                <div className="fixed top-16 left-1/2 -translate-x-1/2 z-[1500] bg-blue-600 text-white px-4 py-2 rounded-full shadow-lg text-sm font-medium flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
                    📍 Click vào vị trí trên bản đồ để chọn
                    <button
                        onClick={() => {
                            setIsPickingOnMap(false);
                            setShowReportModal(true);
                        }}
                        className="ml-2 text-white/80 hover:text-white text-xs underline"
                    >
                        Huỷ
                    </button>
                </div>
            )}

            {/* ── Report modal ── */}
            {showReportModal && (
                <div
                    className="fixed inset-0 z-[2000] bg-black/50 flex items-center justify-center p-4"
                    onClick={handleCloseReportModal}
                >
                    <div
                        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="p-5 border-b border-slate-100 flex items-start justify-between bg-gradient-to-r from-amber-50 to-orange-50">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                                    <Megaphone className="text-amber-600" size={20} />
                                </div>
                                <div>
                                    <h2 className="font-bold text-slate-900 text-lg">
                                        Báo sự cố
                                    </h2>
                                    <p className="text-xs text-slate-500">
                                        Gửi thông tin tới chính quyền
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={handleCloseReportModal}
                                className="p-1 hover:bg-white/60 rounded transition-colors"
                            >
                                <X size={18} />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-5">
                            <IncidentReportForm
                                hideLookup
                                defaultCoordinates={pickedCoords}
                                onPickOnMap={startPickOnMap}
                                isPickingOnMap={isPickingOnMap}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DisasterMap;
