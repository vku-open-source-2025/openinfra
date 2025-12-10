import { useQuery } from "@tanstack/react-query";
import { maintenanceApi } from "../../api/maintenance";
import { incidentsApi } from "../../api/incidents";
import { format } from "date-fns";
import { Skeleton } from "../ui/skeleton";
import { Button } from "../ui/button";
import { Link } from "@tanstack/react-router";
import { ExternalLink, Calendar, User, DollarSign } from "lucide-react";
import type { Asset } from "../../types/asset";

interface AssetOverviewTabProps {
  assetId: string;
  asset: Asset;
}

const AssetOverviewTab: React.FC<AssetOverviewTabProps> = ({ assetId, asset }) => {
  const { data: recentMaintenance, isLoading: maintenanceLoading } = useQuery({
    queryKey: ["maintenance", assetId, "recent"],
    queryFn: () => maintenanceApi.getByAsset(assetId, { limit: 5 }),
  });

  const { data: recentIncidents, isLoading: incidentsLoading } = useQuery({
    queryKey: ["incidents", assetId, "recent"],
    queryFn: () => incidentsApi.list({ asset_id: assetId, limit: 5 }),
  });

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div>
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Thông tin cơ bản</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Tên tài sản</label>
            <p className="text-sm font-medium text-slate-900 mt-1">{asset.name || asset.feature_code}</p>
          </div>
          <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Loại tài sản</label>
            <p className="text-sm font-medium text-slate-900 mt-1">{asset.feature_type}</p>
          </div>
          {asset.managing_unit && (
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Đơn vị quản lý</label>
              <p className="text-sm font-medium text-slate-900 mt-1">{asset.managing_unit}</p>
            </div>
          )}
          {asset.manufacturer && (
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Nhà sản xuất</label>
              <p className="text-sm font-medium text-slate-900 mt-1">{asset.manufacturer}</p>
            </div>
          )}
          {asset.lifecycle?.commissioned_date && (
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Ngày đưa vào sử dụng</label>
              <p className="text-sm font-medium text-slate-900 mt-1">
                {format(new Date(asset.lifecycle.commissioned_date), "dd/MM/yyyy")}
              </p>
            </div>
          )}
          {asset.lifecycle?.designed_lifespan_years && (
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Tuổi thọ thiết kế</label>
              <p className="text-sm font-medium text-slate-900 mt-1">
                {asset.lifecycle.designed_lifespan_years} years
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Status Summary */}
      <div>
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Tóm tắt trạng thái</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <label className="text-xs text-slate-500 uppercase tracking-wide">Trạng thái hiện tại</label>
            <div className="mt-2">
              <span className={`px-2 py-1 text-xs font-bold rounded uppercase ${
                asset.lifecycle?.lifecycle_status === "operational" ? "bg-green-100 text-green-700" :
                asset.lifecycle?.lifecycle_status === "under_repair" ? "bg-yellow-100 text-yellow-700" :
                asset.lifecycle?.lifecycle_status === "damaged" ? "bg-red-100 text-red-700" :
                "bg-gray-100 text-gray-700"
              }`}>
                {asset.lifecycle?.lifecycle_status?.replace("_", " ") || "N/A"}
              </span>
            </div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <label className="text-xs text-slate-500 uppercase tracking-wide">Điểm sức khỏe</label>
            <div className="mt-2">
              <span className="text-lg font-bold text-slate-900">
                {asset.lifecycle?.health_score ?? 0}/100
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="ml-2 text-xs"
                onClick={() => {
                  // Navigate to lifecycle tab
                  const lifecycleTab = document.querySelector('[value="lifecycle"]') as HTMLElement;
                  lifecycleTab?.click();
                }}
              >
                Xem chi tiết
              </Button>
            </div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <label className="text-xs text-slate-500 uppercase tracking-wide">Thời gian còn lại</label>
            <div className="mt-2">
              <span className="text-sm font-semibold text-slate-900">
                {asset.lifecycle?.remaining_lifespan_years
                  ? `${asset.lifecycle.remaining_lifespan_years} năm`
                  : "N/A"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Last 5 Maintenance Records */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">5 bản ghi bảo trì gần đây</h3>
            <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              const maintenanceTab = document.querySelector('[value="maintenance"]') as HTMLElement;
              maintenanceTab?.click();
            }}
          >
            Xem tất cả <ExternalLink size={14} className="ml-1" />
          </Button>
        </div>
        {maintenanceLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : recentMaintenance && recentMaintenance.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Ngày</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Tóm tắt</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Kỹ thuật viên</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Chi phí</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Xem</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {recentMaintenance.map((record) => (
                  <tr key={record.id}>
                    <td className="px-4 py-3 text-sm text-slate-900">
                      {format(new Date(record.scheduled_date), "dd/MM/yyyy")}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-900">{record.title}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{record.technician || "N/A"}</td>
                    <td className="px-4 py-3 text-sm text-slate-900">
                      {record.actual_cost
                        ? `$${record.actual_cost.toLocaleString()}`
                        : record.estimated_cost
                        ? `~$${record.estimated_cost.toLocaleString()}`
                        : "N/A"}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Button variant="ghost" size="sm">Xem</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <p>Không tìm thấy bản ghi bảo trì.</p>
          </div>
        )}
      </div>

      {/* Active / Recent Incidents */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">Sự cố hoạt động / gần đây</h3>
            <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              const incidentsTab = document.querySelector('[value="incidents"]') as HTMLElement;
              incidentsTab?.click();
            }}
          >
            Xem tất cả <ExternalLink size={14} className="ml-1" />
          </Button>
        </div>
        {incidentsLoading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : recentIncidents && recentIncidents.length > 0 ? (
          <div className="space-y-2">
            {recentIncidents.map((incident) => (
              <div
                key={incident.id}
                className="bg-white border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div
                      className={`w-2 h-2 rounded-full mt-2 ${
                        incident.severity === "critical"
                          ? "bg-red-500"
                          : incident.severity === "high"
                          ? "bg-orange-500"
                          : incident.severity === "medium"
                          ? "bg-yellow-500"
                          : "bg-blue-500"
                      }`}
                    />
                    <div className="flex-1">
                      <h4 className="font-medium text-slate-900">{incident.title}</h4>
                      <p className="text-sm text-slate-600 mt-1 line-clamp-2">{incident.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                        <span>Status: {incident.status}</span>
                        <span>Reporter: {incident.reporter_type}</span>
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">Xem</Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <p>Không tìm thấy sự cố.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AssetOverviewTab;
