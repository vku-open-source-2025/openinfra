import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { getAssets, getAssetId, type Asset } from "../api";
import { emergencyApi } from "../api/emergency";
import MapComponent from "../components/Map";
import AssetTable from "../components/AssetTable";
import MaintenanceLogList from "../components/MaintenanceLog";
import StatsCard from "../components/StatsCard";
import CalendarView from "../components/CalendarView";
import { useIoT } from "../hooks/useIoT";
import QRCodeModal from "../components/QRCodeModal";
import NFCWriteModal from "../components/NFCWriteModal";
import { NotificationCenter } from "../components/notifications/NotificationCenter";
import IoTSensorChart from "../components/IoTSensorChart";
import {
    Zap,
    AlertTriangle,
    CheckCircle,
    Activity,
    QrCode,
    Radio,
    MapPin,
    Calendar,
    LayoutDashboard,
} from "lucide-react";

type TabType = "overview" | "calendar";

const pseudoRandom = (seed: number): number => {
    const value = Math.sin(seed) * 10000;
    return value - Math.floor(value);
};

const getPointLatitude = (asset: Asset): number | null => {
    if (
        asset.geometry.type !== "Point" ||
        !Array.isArray(asset.geometry.coordinates) ||
        typeof asset.geometry.coordinates[1] !== "number"
    ) {
        return null;
    }
    return asset.geometry.coordinates[1];
};

const Dashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabType>("overview");
    const {
        data: initialAssets,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["assets"],
        queryFn: getAssets,
    });

    const {
        data: sosconnStatus,
        isLoading: isSosconnStatusLoading,
    } = useQuery({
        queryKey: ["sosconn-status"],
        queryFn: emergencyApi.getSosconnStatus,
        refetchInterval: 30000,
        retry: 1,
    });

    const { data: sosconnActiveEvents = [] } = useQuery({
        queryKey: ["sosconn-active-events"],
        queryFn: async () => {
            const events = await emergencyApi.list({ limit: 200, status: "active" });
            return events.filter((event) => event.source === "sosconn");
        },
        refetchInterval: 45000,
        retry: 1,
    });

    const { assetsWithStatus, alerts } = useIoT(initialAssets);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [routePoints, setRoutePoints] = useState<Asset[]>([]);
    const [showQRModal, setShowQRModal] = useState(false);
    const [showNFCModal, setShowNFCModal] = useState(false);

    const displayAssets = assetsWithStatus || [];

    const handleRouteOptimization = () => {
        if (!displayAssets.length) return;
        const points = [...displayAssets]
            .filter((a) => getPointLatitude(a) !== null)
            .slice(0, 5)
            .sort(
                (a, b) =>
                    (getPointLatitude(b) ?? Number.NEGATIVE_INFINITY) -
                    (getPointLatitude(a) ?? Number.NEGATIVE_INFINITY)
            );
        setRoutePoints(points);
        alert(`Tối ưu tuyến cho ${points.length} điểm dừng!`);
    };

    const fakeCalendarLogs = useMemo(() => {
        if (!initialAssets) return [];
        const logs = [];
        const statuses = ["Pending", "In Progress", "Completed"];
        const now = new Date();
        for (let i = 0; i < 50; i++) {
            const date = new Date(now);
            date.setDate(date.getDate() + Math.floor(pseudoRandom(i + 1) * 60) - 30);
            const sourceAsset =
                initialAssets.length > 0
                    ? initialAssets[i % initialAssets.length]
                    : undefined;
            logs.push({
                _id: `log-${i}`,
                asset_id: sourceAsset ? getAssetId(sourceAsset) : `asset-${i}`,
                scheduled_date: date.toISOString(),
                description: `Maintenance for ${sourceAsset?.feature_code || "Asset"}`,
                status: statuses[Math.floor(pseudoRandom((i + 1) * 17) * statuses.length)],
                technician: "System",
                created_at: now.toISOString(),
            });
        }
        return logs;
    }, [initialAssets]);

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-slate-50">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">Đang tải dữ liệu hệ thống...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 text-center text-red-500">Lỗi khi tải dữ liệu tài sản</div>
        );
    }

    const assetCount = displayAssets.length;
    const activeAlerts = alerts.length + Math.floor(assetCount * 0.02);
    const maintenanceDue = Math.floor(assetCount * 0.12);
    const operationalRate = assetCount > 0 
        ? (((assetCount - activeAlerts) / assetCount) * 100).toFixed(1) 
        : "0.0";

    const sosconnHealthLabel = isSosconnStatusLoading
        ? "Đang kiểm tra"
        : sosconnStatus?.reachable && sosconnStatus?.configured
          ? "Online"
          : "Offline";

    const sosconnCheckedAt = sosconnStatus?.checked_at
        ? new Date(sosconnStatus.checked_at).toLocaleTimeString("vi-VN")
        : "--:--:--";

    return (
        <div className="flex flex-col h-full bg-slate-50 font-sans text-slate-900">
            <main className="flex-1 flex flex-col overflow-hidden relative">
                {/* Alert Feed Overlay */}
                {alerts.length > 0 && (
                    <div className="absolute top-20 right-8 z-50 w-80 pointer-events-none">
                        {alerts.map((alert, idx) => (
                            <div
                                key={idx}
                                className="bg-red-50 border-l-4 border-red-500 p-3 mb-2 shadow-lg rounded-r animate-in slide-in-from-right fade-in duration-300 pointer-events-auto flex items-start gap-3"
                            >
                                <AlertTriangle className="text-red-500 shrink-0" size={18} />
                                <p className="text-xs font-medium text-red-800">{alert}</p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Header */}
                <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800">Bảng điều khiển</h2>
                        <p className="text-sm text-slate-500">Tổng quan hệ thống và hiệu suất tài sản</p>
                    </div>
                    <div className="flex gap-3 items-center">
                        <NotificationCenter />
                        <Link
                            to="/admin/map"
                            search={{ assetId: undefined }}
                            className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                        >
                            <MapPin size={16} />
                            Mở bản đồ
                        </Link>
                        <button className="px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium text-white hover:bg-blue-700 shadow-sm flex items-center gap-2">
                            <Zap size={16} />
                            Thêm tài sản
                        </button>
                    </div>
                </header>

                {/* Tab Navigation */}
                <div className="bg-white border-b border-slate-200 px-8">
                    <nav className="flex gap-6">
                        <button
                            onClick={() => setActiveTab("overview")}
                            className={`py-3 px-1 border-b-2 text-sm font-medium flex items-center gap-2 transition-colors ${
                                activeTab === "overview"
                                    ? "border-blue-600 text-blue-600"
                                    : "border-transparent text-slate-500 hover:text-slate-700"
                            }`}
                        >
                            <LayoutDashboard size={16} />
                            Tổng quan
                        </button>
                        <button
                            onClick={() => setActiveTab("calendar")}
                            className={`py-3 px-1 border-b-2 text-sm font-medium flex items-center gap-2 transition-colors ${
                                activeTab === "calendar"
                                    ? "border-blue-600 text-blue-600"
                                    : "border-transparent text-slate-500 hover:text-slate-700"
                            }`}
                        >
                            <Calendar size={16} />
                            Lịch bảo trì
                        </button>
                    </nav>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8">
                    {activeTab === "calendar" ? (
                        <CalendarView logs={fakeCalendarLogs} />
                    ) : (
                        <>
                            {/* Stats Row */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
                                <StatsCard
                                    title="Tổng tài sản"
                                    value={assetCount}
                                    icon={Zap}
                                    color="bg-blue-500"
                                    trend="12%"
                                    trendUp={true}
                                />
                                <StatsCard
                                    title="Cảnh báo đang hoạt động"
                                    value={activeAlerts}
                                    icon={AlertTriangle}
                                    color="bg-red-500"
                                    trend="2"
                                    trendUp={false}
                                />
                                <StatsCard
                                    title="Bảo trì sắp tới"
                                    value={maintenanceDue}
                                    icon={Activity}
                                    color="bg-amber-500"
                                    trend="5%"
                                    trendUp={false}
                                />
                                <StatsCard
                                    title="Tỷ lệ hoạt động"
                                    value={`${operationalRate}%`}
                                    icon={CheckCircle}
                                    color="bg-green-500"
                                    trend="0.5%"
                                    trendUp={true}
                                />
                                <StatsCard
                                    title="SOSConn / Copilot"
                                    value={sosconnHealthLabel}
                                    icon={Radio}
                                    color="bg-cyan-500"
                                />
                            </div>

                            <div className="mb-8 rounded-xl border border-cyan-200 bg-cyan-50/70 p-4">
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                    <div>
                                        <p className="text-sm font-semibold text-cyan-900">SOSConn Integration</p>
                                        <p className="text-xs text-cyan-800">
                                            Trạng thái: {sosconnHealthLabel} • Provider: {sosconnStatus?.provider || "github-copilot"}
                                            {sosconnStatus?.model ? ` • Model: ${sosconnStatus.model}` : ""}
                                        </p>
                                        <p className="text-xs text-cyan-700 mt-1">
                                            Active SOSConn events: {sosconnActiveEvents.length} • Last check: {sosconnCheckedAt}
                                        </p>
                                        {sosconnStatus?.detail ? (
                                            <p className="text-xs text-red-700 mt-1">Chi tiet ket noi: {sosconnStatus.detail}</p>
                                        ) : null}
                                    </div>
                                    <Link
                                        to="/admin/emergency-center"
                                        className="px-3 py-2 rounded-lg border border-cyan-300 bg-white text-cyan-800 text-sm font-medium hover:bg-cyan-100"
                                    >
                                        Mo SOSConn Command Center
                                    </Link>
                                </div>
                            </div>

                            {/* Main Content Grid */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[600px]">
                                {/* Left Column: Map & Asset List */}
                                <div className="lg:col-span-2 flex flex-col gap-6 h-full overflow-hidden">
                                    {/* Map Preview */}
                                    <div className="bg-white p-1 rounded-xl shadow-sm border border-slate-200 h-[60%] shrink-0 relative">
                                        <MapComponent
                                            assets={displayAssets}
                                            onAssetSelect={setSelectedAsset}
                                            routePoints={routePoints}
                                            selectedAsset={selectedAsset}
                                            className="h-full"
                                        />
                                        <button
                                            onClick={handleRouteOptimization}
                                            className="absolute bottom-4 right-4 px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2 shadow-sm"
                                        >
                                            <Activity size={14} />
                                            Tối ưu lộ trình
                                        </button>
                                    </div>

                                    {/* Asset Table */}
                                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 flex-1 overflow-hidden flex flex-col min-h-0">
                                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                                            <h3 className="font-bold text-lg">Tài sản gần đây</h3>
                                        </div>
                                        <div className="flex-1 overflow-y-auto">
                                            <AssetTable
                                                assets={displayAssets}
                                                onAssetSelect={setSelectedAsset}
                                                selectedAssetId={selectedAsset ? getAssetId(selectedAsset) : undefined}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Right Column: Asset Details Panel */}
                                <div className="bg-white rounded-xl shadow-sm border border-slate-200 h-full overflow-hidden flex flex-col">
                                    {selectedAsset ? (
                                        <>
                                            <div className="p-6 border-b border-slate-100 bg-slate-50">
                                                <div className="flex items-center gap-3 mb-1">
                                                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase tracking-wide">
                                                        {selectedAsset.feature_code}
                                                    </span>
                                                    <span className="text-xs text-slate-400">
                                                        ID: {getAssetId(selectedAsset).slice(-6)}
                                                    </span>
                                                    {(selectedAsset as Asset & { status?: string }).status && (
                                                        <span
                                                            className={`px-2 py-1 text-xs font-bold rounded uppercase tracking-wide ${
                                                                (selectedAsset as Asset & { status?: string }).status === "Online"
                                                                    ? "bg-green-100 text-green-700"
                                                                    : "bg-red-100 text-red-700"
                                                            }`}
                                                        >
                                                            {(selectedAsset as Asset & { status?: string }).status}
                                                        </span>
                                                    )}
                                                </div>
                                                <h3 className="text-xl font-bold text-slate-900">
                                                    {selectedAsset.feature_type}
                                                </h3>
                                            </div>

                                            <div className="flex-1 overflow-y-auto p-6">
                                                <div className="space-y-6">
                                                    {/* Location Info */}
                                                    <div>
                                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                                            Vị trí
                                                        </h4>
                                                        <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                                            {selectedAsset.geometry.type === "Point" &&
                                                            Array.isArray(selectedAsset.geometry.coordinates) &&
                                                            typeof selectedAsset.geometry.coordinates[0] === "number" ? (
                                                                <div className="grid grid-cols-2 gap-4 text-sm">
                                                                    <div>
                                                                        <p className="text-slate-500 text-xs">Vĩ độ</p>
                                                                        <p className="font-mono font-medium">
                                                                            {(selectedAsset.geometry.coordinates as number[])[1].toFixed(6)}
                                                                        </p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-slate-500 text-xs">Kinh độ</p>
                                                                        <p className="font-mono font-medium">
                                                                            {(selectedAsset.geometry.coordinates as number[])[0].toFixed(6)}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            ) : (
                                                                <div className="text-sm">
                                                                    <p className="text-slate-500 text-xs mb-1">Loại hình học</p>
                                                                    <p className="font-mono font-medium mb-2">
                                                                        {selectedAsset.geometry.type}
                                                                    </p>
                                                                    <p className="text-slate-500 text-xs mb-1">Chi tiết</p>
                                                                    <p className="font-mono font-medium">
                                                                        {selectedAsset.geometry.type === "LineString"
                                                                            ? `${selectedAsset.geometry.coordinates.length} points`
                                                                            : "Complex Geometry"}
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
                                                        <MaintenanceLogList assetId={getAssetId(selectedAsset)} />
                                                    </div>

                                                    {/* IoT Sensor Data */}
                                                    <div>
                                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                                            Dữ liệu cảm biến IoT
                                                        </h4>
                                                        <IoTSensorChart
                                                            assetId={getAssetId(selectedAsset)}
                                                            assetName={selectedAsset.feature_type}
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Action Buttons */}
                                            <div className="p-4 border-t border-slate-100 bg-slate-50 flex flex-col gap-2">
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => setShowQRModal(true)}
                                                        className="flex-1 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm flex items-center justify-center gap-2"
                                                    >
                                                        <QrCode size={16} />
                                                        QR Code
                                                    </button>
                                                    <button
                                                        onClick={() => setShowNFCModal(true)}
                                                        className="flex-1 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm flex items-center justify-center gap-2"
                                                    >
                                                        <Radio size={16} />
                                                        Write NFC
                                                    </button>
                                                </div>
                                                <button className="w-full py-2 bg-blue-600 border border-transparent rounded-lg text-sm font-medium text-white hover:bg-blue-700 shadow-sm">
                                                    Lên lịch bảo trì
                                                </button>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                                            <div className="bg-slate-100 p-4 rounded-full mb-4">
                                                <Activity size={32} className="text-slate-300" />
                                            </div>
                                            <p className="font-medium text-slate-500">Chưa có tài sản được chọn</p>
                                            <p className="text-sm mt-2">
                                                Chọn một tài sản từ bản đồ hoặc danh sách để xem chi tiết và lịch sử bảo trì.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </>
                    )}
                </div>

                {/* Modals */}
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
            </main>
        </div>
    );
};

export default Dashboard;
