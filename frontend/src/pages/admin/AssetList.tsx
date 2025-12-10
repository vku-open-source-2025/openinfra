import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { MapPin, Plus, Search } from "lucide-react";
import { useState } from "react";
import { assetsApi } from "../../api/assets";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";

const AssetList: React.FC = () => {
    const navigate = useNavigate();
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("");

    const {
        data: assets,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["assets", "list", statusFilter],
        queryFn: () => assetsApi.list({ status: statusFilter || undefined }),
    });

    const filteredAssets = assets?.filter((asset) => {
        if (!search) return true;
        const searchLower = search.toLowerCase();
        return (
            asset.name?.toLowerCase().includes(searchLower) ||
            asset.feature_code.toLowerCase().includes(searchLower) ||
            asset.feature_type.toLowerCase().includes(searchLower)
        );
    });

    if (error) {
        return (
            <div className="p-6">
                <div className="text-center py-12 text-red-500">
                    Lỗi tải danh sách tài sản. Vui lòng thử lại.
                </div>
            </div>
        );
    }

    const renderLifecycle = (value?: string) => {
        if (!value) return "";
        switch (value) {
            case "operational":
                return "Đang vận hành";
            case "under_repair":
                return "Đang sửa chữa";
            case "damaged":
                return "Hư hỏng";
            case "decommissioned":
                return "Ngưng sử dụng";
            default:
                return value;
        }
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                        Tài sản
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Quản lý tài sản hạ tầng
                    </p>
                </div>
                <Button
                    onClick={() => {
                        // TODO: Navigate to asset create
                        console.log("Create asset");
                    }}
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Tạo tài sản
                </Button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <div className="relative">
                            <Search
                                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400"
                                size={18}
                            />
                            <Input
                                type="text"
                                placeholder="Tìm kiếm tài sản..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="pl-10"
                            />
                        </div>
                    </div>
                    <div className="w-full md:w-48">
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                        >
                            <option value="">Tất cả trạng thái</option>
                            <option value="operational">Đang vận hành</option>
                            <option value="under_repair">Đang sửa chữa</option>
                            <option value="damaged">Hư hỏng</option>
                            <option value="decommissioned">
                                Ngưng sử dụng
                            </option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Asset List */}
            {isLoading ? (
                <div className="space-y-4">
                    {[...Array(10)].map((_, i) => (
                        <Skeleton key={i} className="h-24 w-full" />
                    ))}
                </div>
            ) : filteredAssets && filteredAssets.length > 0 ? (
                <div className="space-y-3">
                    {filteredAssets.map((asset) => (
                        <div
                            key={asset.id}
                            onClick={() =>
                                navigate({
                                    to: `/admin/assets/${
                                        asset._id || asset.id
                                    }`,
                                })
                            }
                            className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4 flex-1">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="font-semibold text-slate-900">
                                                {asset.name ||
                                                    asset.feature_type}
                                            </h3>
                                            <span
                                                className={`px-2 py-1 text-xs font-bold rounded uppercase ${
                                                    asset.lifecycle
                                                        ?.lifecycle_status ===
                                                    "operational"
                                                        ? "bg-green-100 text-green-700"
                                                        : asset.lifecycle
                                                              ?.lifecycle_status ===
                                                          "under_repair"
                                                        ? "bg-yellow-100 text-yellow-700"
                                                        : asset.lifecycle
                                                              ?.lifecycle_status ===
                                                          "damaged"
                                                        ? "bg-red-100 text-red-700"
                                                        : "bg-gray-100 text-gray-700"
                                                }`}
                                            >
                                                {renderLifecycle(
                                                    asset.lifecycle?.lifecycle_status || asset.status
                                                )}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-slate-600">
                                            <span>
                                                Mã: {asset.feature_code}
                                            </span>
                                            <span>
                                                Loại: {asset.feature_type}
                                            </span>
                                            {asset.location && (
                                                <span className="flex items-center gap-1">
                                                    <MapPin size={14} />
                                                    {asset.location.address ||
                                                        (asset.geometry?.coordinates &&
                                                         Array.isArray(asset.geometry.coordinates) &&
                                                         asset.geometry.coordinates.length >= 2 &&
                                                         typeof asset.geometry.coordinates[0] === 'number' &&
                                                         typeof asset.geometry.coordinates[1] === 'number'
                                                            ? `${asset.geometry.coordinates[1].toFixed(4)}, ${asset.geometry.coordinates[0].toFixed(4)}`
                                                            : 'N/A')}
                                                </span>
                                            )}
                                        </div>
                                        {asset.lifecycle?.health_score !==
                                            undefined && (
                                            <div className="mt-2">
                                                <span className="text-xs text-slate-500">
                                                    Điểm sức khỏe:{" "}
                                                </span>
                                                <span
                                                    className={`text-sm font-semibold ${
                                                        asset.lifecycle
                                                            .health_score >= 80
                                                            ? "text-green-600"
                                                            : asset.lifecycle
                                                                  .health_score >=
                                                              60
                                                            ? "text-yellow-600"
                                                            : asset.lifecycle
                                                                  .health_score >=
                                                              40
                                                            ? "text-orange-600"
                                                            : "text-red-600"
                                                    }`}
                                                >
                                                    {
                                                        asset.lifecycle
                                                            .health_score
                                                    }
                                                    /100
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-12 text-slate-500">
                    <p>Không tìm thấy tài sản.</p>
                </div>
            )}
        </div>
    );
};

export default AssetList;
