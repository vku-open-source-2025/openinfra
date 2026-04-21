import React, { useState, useCallback, useMemo } from "react";
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
    Crosshair,
    Home,
    Siren,
} from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchTileConfig } from "../lib/tileConfig";
import VndmsHazardLayer, { VndmsLegend } from "../components/VndmsHazardLayer";
import { useVndmsHazards, type VndmsHazard } from "../hooks/useVndmsHazards";
import HazardMarkersLayer from "../components/HazardMarkersLayer";
import EmergencyEventsLayer from "../components/EmergencyEventsLayer";
import { hazardsApi } from "../api/hazards";
import { usePublicEmergencyEvents } from "../hooks/usePublicEmergencyEvents";
import IncidentReportForm from "../components/IncidentReportForm";
import type { Hazard } from "../types/hazard";
import type {
    PublicEmergencyEvent,
    EmergencyEventType,
    EmergencySeverity,
} from "../types/emergency";

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
    critical: "bg-purple-100 text-purple-800",
};

const SEVERITY_LABEL: Record<string, string> = {
    low: "Thấp",
    medium: "Trung bình",
    high: "Cao",
    critical: "Nghiêm trọng",
};

const EVENT_TYPE_LABEL: Record<EmergencyEventType, string> = {
    flood: "Lũ lụt",
    storm: "Bão",
    landslide: "Sạt lở",
    fire: "Cháy rừng",
    earthquake: "Động đất",
    outage: "Mất điện",
    pollution: "Ô nhiễm",
    other: "Khác",
};

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

function haversineKm(
    a: { lat: number; lng: number },
    b: { lat: number; lng: number }
): number {
    const R = 6371;
    const toRad = (d: number) => (d * Math.PI) / 180;
    const dLat = toRad(b.lat - a.lat);
    const dLng = toRad(b.lng - a.lng);
    const lat1 = toRad(a.lat);
    const lat2 = toRad(b.lat);
    const x =
        Math.sin(dLat / 2) ** 2 +
        Math.sin(dLng / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2);
    return 2 * R * Math.asin(Math.sqrt(x));
}

function pointFromHazard(h: Hazard): { lat: number; lng: number } | null {
    if (!h.geometry?.coordinates) return null;
    if (h.geometry.type === "Point") {
        const [lng, lat] = h.geometry.coordinates as number[];
        if (typeof lat === "number" && typeof lng === "number") return { lat, lng };
    }
    return null;
}

function pointFromEvent(e: PublicEmergencyEvent): { lat: number; lng: number } | null {
    if (!e.geometry?.coordinates) return null;
    if (e.geometry.type === "Point") {
        const [lng, lat] = e.geometry.coordinates as number[];
        if (typeof lat === "number" && typeof lng === "number") return { lat, lng };
    }
    return null;
}

const VIETNAM_CENTER: [number, number] = [16.0, 107.0];
const NEAR_ME_RADIUS_KM = 10;

type FilterChip = "all" | "critical" | "near";

// ── Cards ────────────────────────────────────────────────────────────────────

const EventCard: React.FC<{
    event: PublicEmergencyEvent;
    onLocate: (e: PublicEmergencyEvent) => void;
}> = ({ event, onLocate }) => {
    const sevColor =
        event.severity === "critical"
            ? "#7c3aed"
            : event.severity === "high"
            ? "#ef4444"
            : event.severity === "medium"
            ? "#f59e0b"
            : "#22c55e";
    const loc = event.location;
    const locText = [loc?.address, loc?.ward, loc?.district, loc?.city]
        .filter(Boolean)
        .join(", ");
    const startedAt = event.started_at ?? event.created_at;
    const hasGeom = !!pointFromEvent(event);
    return (
        <div
            className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden border-l-4"
            style={{ borderLeftColor: sevColor }}
        >
            <div className="p-3 flex items-start gap-2.5">
                <span className="text-xl flex-shrink-0 mt-0.5">🚨</span>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap mb-1">
                        <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                SEVERITY_BG[event.severity] ?? "bg-slate-100 text-slate-700"
                            }`}
                        >
                            {SEVERITY_LABEL[event.severity] ?? event.severity}
                        </span>
                        <span className="text-[10px] text-slate-500">
                            {EVENT_TYPE_LABEL[event.event_type] ?? event.event_type}
                        </span>
                        <span className="text-[10px] text-red-600 font-semibold">
                            • Đang triển khai
                        </span>
                    </div>
                    <h3 className="font-semibold text-slate-900 text-sm leading-snug">
                        {event.title}
                    </h3>
                    {locText && (
                        <p className="text-xs text-slate-500 mt-0.5">📍 {locText}</p>
                    )}
                    {startedAt && (
                        <p className="text-[10px] text-slate-400 mt-0.5">
                            Bắt đầu: {timeAgo(new Date(startedAt).getTime())}
                        </p>
                    )}
                </div>
                <button
                    onClick={() => onLocate(event)}
                    disabled={!hasGeom}
                    title={hasGeom ? "Xem trên bản đồ" : "Không có tọa độ"}
                    className="flex-shrink-0 p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <MapPin size={14} />
                </button>
            </div>
        </div>
    );
};

const VndmsCard: React.FC<{
    hazard: VndmsHazard;
    onLocate: (h: VndmsHazard) => void;
}> = ({ hazard, onLocate }) => (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
        <div className="p-3 flex items-start gap-2.5">
            <span className="text-xl flex-shrink-0 mt-0.5">
                {TYPE_EMOJI[hazard.warning_type] ?? "⚠️"}
            </span>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap mb-1">
                    <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            SEVERITY_BG[hazard.severity] ?? "bg-slate-100 text-slate-700"
                        }`}
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
);

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
                    <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            SEVERITY_BG[hazard.severity as EmergencySeverity] ??
                            "bg-slate-100 text-slate-700"
                        }`}
                    >
                        {SEVERITY_LABEL[hazard.severity] ?? hazard.severity}
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

// ── Main page ────────────────────────────────────────────────────────────────

const DisasterMap: React.FC = () => {
    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const mapRef = React.useRef<L.Map | null>(null);
    const [leafletMap, setLeafletMap] = useState<L.Map | null>(null);

    const [filterChip, setFilterChip] = useState<FilterChip>("all");
    const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(
        null
    );
    const [geoError, setGeoError] = useState<string | null>(null);
    const [focusedEventId, setFocusedEventId] = useState<string | null>(null);
    const [focusEventNonce, setFocusEventNonce] = useState(0);
    const [focusedHazardId, setFocusedHazardId] = useState<string | null>(null);
    const [focusHazardNonce, setFocusHazardNonce] = useState(0);

    const [showReportModal, setShowReportModal] = useState(false);
    const [isPickingOnMap, setIsPickingOnMap] = useState(false);
    const [pickedCoords, setPickedCoords] = useState<
        { latitude: number; longitude: number } | undefined
    >(undefined);
    const pickedMarkerRef = React.useRef<L.Marker | null>(null);
    const userMarkerRef = React.useRef<L.Marker | null>(null);

    const {
        data: vndmsHazards = [],
        isLoading: vndmsLoading,
        refetch: refetchVndms,
        isFetching: vndmsFetching,
        dataUpdatedAt: vndmsUpdatedAt,
    } = useVndmsHazards(true);

    const {
        data: storedHazards = [],
        refetch: refetchStored,
    } = useQuery({
        queryKey: ["hazards", "active-public"],
        queryFn: () => hazardsApi.list({ is_active: true, limit: 200 }),
        staleTime: 60_000,
        refetchInterval: 5 * 60_000,
    });

    const { data: publicEvents = [], refetch: refetchEvents } =
        usePublicEmergencyEvents(true, 100);

    // Initialize the map
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
    const filteredVndms = useMemo(() => {
        let arr = vndmsHazards;
        if (filterChip === "critical") {
            arr = arr.filter((h) => h.severity === "high");
        } else if (filterChip === "near" && userLocation) {
            arr = arr.filter(
                (h) =>
                    haversineKm(userLocation, { lat: h.lat, lng: h.lon }) <=
                    NEAR_ME_RADIUS_KM
            );
        }
        return arr;
    }, [vndmsHazards, filterChip, userLocation]);

    const filteredStored = useMemo(() => {
        let arr = storedHazards;
        if (filterChip === "critical") {
            arr = arr.filter(
                (h) => h.severity === "critical" || h.severity === "high"
            );
        } else if (filterChip === "near" && userLocation) {
            arr = arr.filter((h) => {
                const p = pointFromHazard(h);
                if (!p) return false;
                return haversineKm(userLocation, p) <= NEAR_ME_RADIUS_KM;
            });
        }
        return arr;
    }, [storedHazards, filterChip, userLocation]);

    const filteredEvents = useMemo(() => {
        let arr = publicEvents;
        if (filterChip === "critical") {
            arr = arr.filter(
                (e) => e.severity === "critical" || e.severity === "high"
            );
        } else if (filterChip === "near" && userLocation) {
            arr = arr.filter((e) => {
                const p = pointFromEvent(e);
                if (!p) return false;
                return haversineKm(userLocation, p) <= NEAR_ME_RADIUS_KM;
            });
        }
        return arr;
    }, [publicEvents, filterChip, userLocation]);

    const handleLocateVndms = useCallback(
        (h: VndmsHazard) => {
            if (!leafletMap) return;
            leafletMap.flyTo([h.lat, h.lon], 11, { animate: true, duration: 1.2 });
        },
        [leafletMap]
    );

    const handleLocateStored = useCallback(
        (h: Hazard) => {
            const p = pointFromHazard(h);
            if (!leafletMap || !p) return;
            leafletMap.flyTo([p.lat, p.lng], 14, { animate: true, duration: 1.2 });
            setFocusedHazardId(h.id);
            setFocusHazardNonce((n) => n + 1);
        },
        [leafletMap]
    );

    const handleLocateEvent = useCallback(
        (e: PublicEmergencyEvent) => {
            const p = pointFromEvent(e);
            if (!leafletMap || !p) return;
            leafletMap.flyTo([p.lat, p.lng], 13, { animate: true, duration: 1.2 });
            setFocusedEventId(e.id);
            setFocusEventNonce((n) => n + 1);
        },
        [leafletMap]
    );

    const totalAlerts =
        publicEvents.length + storedHazards.length + vndmsHazards.length;
    const isFetchingAny = vndmsFetching;

    const handleRefreshAll = useCallback(() => {
        refetchVndms();
        refetchStored();
        refetchEvents();
    }, [refetchVndms, refetchStored, refetchEvents]);

    // ── Geolocation ──────────────────────────────────────────────────────────
    const handleLocateMe = useCallback(() => {
        if (!navigator.geolocation) {
            setGeoError("Trình duyệt không hỗ trợ định vị");
            return;
        }
        setGeoError(null);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                setUserLocation(loc);
                if (leafletMap) {
                    leafletMap.flyTo([loc.lat, loc.lng], 13, {
                        animate: true,
                        duration: 1.2,
                    });
                    if (userMarkerRef.current) {
                        userMarkerRef.current.setLatLng([loc.lat, loc.lng]);
                    } else {
                        const icon = L.divIcon({
                            className: "",
                            html: `<div style="
                                width:18px;height:18px;border-radius:50%;
                                background:#2563eb;
                                border:3px solid white;
                                box-shadow:0 0 0 3px rgba(37,99,235,0.35);
                            "></div>`,
                            iconSize: [18, 18],
                            iconAnchor: [9, 9],
                        });
                        userMarkerRef.current = L.marker([loc.lat, loc.lng], { icon }).addTo(
                            leafletMap
                        );
                    }
                }
            },
            (err) => {
                setGeoError(err.message || "Không lấy được vị trí");
            },
            { enableHighAccuracy: true, timeout: 10_000 }
        );
    }, [leafletMap]);

    // ── Pick-on-map handlers (for incident report) ───────────────────────────
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
        setShowReportModal(false);
    }, []);

    React.useEffect(() => {
        if (!leafletMap || !isPickingOnMap) return;
        const container = leafletMap.getContainer();
        const prevCursor = container.style.cursor;
        container.style.cursor = "crosshair";

        const handler = (e: L.LeafletMouseEvent) => {
            const { lat, lng } = e.latlng;
            setPickedCoords({ latitude: lat, longitude: lng });
            placePickedMarker(lat, lng);
            setIsPickingOnMap(false);
            setShowReportModal(true);
        };
        leafletMap.on("click", handler);
        return () => {
            leafletMap.off("click", handler);
            container.style.cursor = prevCursor;
        };
    }, [leafletMap, isPickingOnMap, placePickedMarker]);

    const handleCloseReportModal = useCallback(() => {
        setShowReportModal(false);
        setIsPickingOnMap(false);
        if (pickedMarkerRef.current && leafletMap) {
            leafletMap.removeLayer(pickedMarkerRef.current);
            pickedMarkerRef.current = null;
        }
        setPickedCoords(undefined);
    }, [leafletMap]);

    // ── Render ────────────────────────────────────────────────────────────────
    const eventsForLayer = useMemo(
        () => publicEvents.filter((e) => !!pointFromEvent(e)),
        [publicEvents]
    );

    const hasNoAlerts = totalAlerts === 0;

    return (
        <div className="flex flex-col h-screen bg-slate-50 font-sans text-slate-900">
            {/* ── Top bar (red gradient, citizen-first) ── */}
            <header className="bg-gradient-to-r from-red-600 via-red-500 to-orange-500 text-white px-4 py-3 flex items-center gap-3 z-50 relative shadow-md">
                <Link to="/" className="hidden sm:block">
                    <h1 className="text-lg font-bold text-white drop-shadow-sm">
                        OpenInfra
                    </h1>
                </Link>
                <div className="hidden sm:block w-px h-6 bg-white/30" />

                <div className="flex items-center gap-2">
                    <Siren className="text-white" size={22} />
                    <div>
                        <h2 className="font-bold text-white text-sm sm:text-base leading-tight">
                            Cảnh báo thiên tai khu vực của bạn
                        </h2>
                        <p className="text-[11px] text-white/80 hidden sm:block">
                            Cập nhật theo thời gian thực · Dành cho người dân
                        </p>
                    </div>
                </div>

                <div className="ml-auto flex items-center gap-2">
                    <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-white/15 backdrop-blur border border-white/30 rounded-full text-white text-xs font-bold">
                        <AlertTriangle size={13} />
                        <span>{totalAlerts}</span>
                        <span className="font-medium opacity-90">cảnh báo</span>
                    </div>
                    <button
                        onClick={handleLocateMe}
                        title="Xác định vị trí của tôi"
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25 text-white text-sm font-semibold border border-white/30 transition-colors"
                    >
                        <Crosshair size={14} />
                        <span className="hidden md:inline">Vị trí tôi</span>
                    </button>
                    <a
                        href="tel:114"
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-red-600 text-sm font-bold hover:bg-red-50 transition-colors shadow"
                        title="Gọi cứu hỏa khẩn cấp"
                    >
                        <Phone size={14} />
                        <span>114</span>
                    </a>
                    <button
                        onClick={handleRefreshAll}
                        disabled={isFetchingAny}
                        title="Làm mới"
                        className="p-2 rounded-lg text-white hover:bg-white/15 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw
                            size={16}
                            className={isFetchingAny ? "animate-spin" : ""}
                        />
                    </button>
                </div>
            </header>

            {/* ── Body: full-width map + floating right panel ── */}
            <div className="flex-1 relative overflow-hidden">
                <div ref={containerRef} className="w-full h-full" />

                {leafletMap && filteredVndms.length > 0 && (
                    <VndmsHazardLayer map={leafletMap} hazards={filteredVndms} />
                )}
                {leafletMap && filteredStored.length > 0 && (
                    <HazardMarkersLayer
                        map={leafletMap}
                        hazards={filteredStored}
                        focusedHazardId={focusedHazardId}
                        focusNonce={focusHazardNonce}
                    />
                )}
                {leafletMap && eventsForLayer.length > 0 && (
                    <EmergencyEventsLayer
                        map={leafletMap}
                        events={eventsForLayer}
                        focusedEventId={focusedEventId}
                        focusNonce={focusEventNonce}
                    />
                )}

                {/* Legend bottom-left */}
                <div className="absolute bottom-24 left-4 z-[1000]">
                    <VndmsLegend />
                </div>

                {/* Floating right panel */}
                <aside className="absolute top-3 right-3 bottom-24 w-full max-w-[22rem] z-[1000] flex flex-col bg-white/95 backdrop-blur rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
                    {/* Filter chips */}
                    <div className="p-3 border-b border-slate-100 shrink-0">
                        <div className="flex gap-1.5">
                            {(
                                [
                                    { key: "all", label: "Tất cả" },
                                    { key: "critical", label: "Nghiêm trọng" },
                                    { key: "near", label: "Gần tôi" },
                                ] as const
                            ).map((chip) => {
                                const disabled =
                                    chip.key === "near" && !userLocation;
                                const active = filterChip === chip.key;
                                return (
                                    <button
                                        key={chip.key}
                                        onClick={() => {
                                            if (chip.key === "near" && !userLocation) {
                                                handleLocateMe();
                                                return;
                                            }
                                            setFilterChip(chip.key);
                                        }}
                                        disabled={disabled && filterChip !== chip.key}
                                        title={
                                            disabled
                                                ? "Cho phép định vị để dùng bộ lọc này"
                                                : undefined
                                        }
                                        className={`flex-1 text-xs font-semibold px-2 py-1.5 rounded-lg border transition-colors ${
                                            active
                                                ? "bg-red-600 text-white border-red-600"
                                                : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                                        } ${
                                            disabled && !active
                                                ? "opacity-60 cursor-not-allowed"
                                                : ""
                                        }`}
                                    >
                                        {chip.label}
                                    </button>
                                );
                            })}
                        </div>
                        {geoError && (
                            <p className="text-[11px] text-red-600 mt-1.5">{geoError}</p>
                        )}
                        <div className="flex items-center gap-1 text-[11px] text-slate-500 mt-2">
                            <Clock size={11} />
                            {vndmsLoading ? (
                                "Đang tải..."
                            ) : (
                                <>
                                    <span>
                                        {filteredEvents.length} chiến dịch ·{" "}
                                        {filteredStored.length + filteredVndms.length}{" "}
                                        cảnh báo
                                    </span>
                                    {vndmsUpdatedAt > 0 && (
                                        <span className="ml-auto text-slate-400">
                                            {timeAgo(vndmsUpdatedAt)}
                                        </span>
                                    )}
                                </>
                            )}
                        </div>
                    </div>

                    {/* List sections */}
                    <div className="flex-1 overflow-y-auto p-3 space-y-4">
                        {/* Section 1: ongoing rescue operations */}
                        <section>
                            <h3 className="text-[11px] uppercase font-bold tracking-wide text-red-600 mb-2 flex items-center gap-1">
                                🚨 Chiến dịch cứu hộ đang diễn ra
                            </h3>
                            {filteredEvents.length === 0 ? (
                                <div className="text-[11px] text-slate-400 italic py-2">
                                    Không có chiến dịch nào đang diễn ra
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {filteredEvents.map((e) => (
                                        <EventCard
                                            key={e.id}
                                            event={e}
                                            onLocate={handleLocateEvent}
                                        />
                                    ))}
                                </div>
                            )}
                        </section>

                        {/* Section 2: hazards 24h */}
                        <section>
                            <h3 className="text-[11px] uppercase font-bold tracking-wide text-amber-700 mb-2 flex items-center gap-1">
                                ⚠️ Cảnh báo thiên tai
                            </h3>
                            {hasNoAlerts ? (
                                <div className="text-center py-6 text-slate-400">
                                    <ShieldAlert
                                        size={28}
                                        className="mx-auto mb-2 opacity-30"
                                    />
                                    <p className="text-sm text-emerald-700 font-semibold">
                                        Khu vực bạn hiện an toàn ✓
                                    </p>
                                </div>
                            ) : filteredStored.length + filteredVndms.length === 0 ? (
                                <div className="text-[11px] text-slate-400 italic py-2">
                                    Không có cảnh báo phù hợp bộ lọc
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {filteredStored.map((h) => (
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
                                </div>
                            )}
                        </section>
                    </div>
                </aside>

                {/* Bottom CTA bar */}
                <div className="absolute bottom-3 left-3 right-3 z-[1000] flex justify-center pointer-events-none">
                    <div className="bg-white/95 backdrop-blur rounded-2xl border border-slate-200 shadow-xl p-2 flex gap-2 pointer-events-auto">
                        <a
                            href="tel:114"
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-600 text-white font-bold hover:bg-red-700 transition-colors shadow-sm"
                        >
                            <Phone size={16} />
                            <span className="text-sm">Gọi 114</span>
                        </a>
                        <button
                            onClick={() => setShowReportModal(true)}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 text-white font-bold hover:bg-amber-600 transition-colors shadow-sm"
                        >
                            <Megaphone size={16} />
                            <span className="text-sm">Báo sự cố</span>
                        </button>
                        <button
                            disabled
                            title="Sắp ra mắt"
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 text-slate-500 font-bold cursor-not-allowed"
                        >
                            <Home size={16} />
                            <span className="text-sm">Nơi trú ẩn gần</span>
                        </button>
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
