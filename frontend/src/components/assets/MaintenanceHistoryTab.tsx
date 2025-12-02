import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { maintenanceApi } from "../../api/maintenance";
import { format } from "date-fns";
import { Skeleton } from "../ui/skeleton";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Select } from "../ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Clock, CheckCircle, AlertCircle, Calendar, X, Download, User, DollarSign } from "lucide-react";
import type { Maintenance, MaintenanceFilterParams } from "../../types/maintenance";
import { MaintenanceApproval } from "../maintenance/MaintenanceApproval";

interface MaintenanceHistoryTabProps {
  assetId: string;
}

const MaintenanceHistoryTab: React.FC<MaintenanceHistoryTabProps> = ({ assetId }) => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<MaintenanceFilterParams>({
    asset_id: assetId,
    limit: 50,
  });
  const [selectedRecord, setSelectedRecord] = useState<Maintenance | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [technicianFilter, setTechnicianFilter] = useState("");
  const [costMin, setCostMin] = useState("");
  const [costMax, setCostMax] = useState("");

  const { data: maintenanceHistory, isLoading } = useQuery({
    queryKey: ["maintenance", "history", assetId, filters],
    queryFn: () => maintenanceApi.getHistory(assetId, filters),
  });

  const applyFilters = () => {
    setFilters({
      asset_id: assetId,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      technician: technicianFilter || undefined,
      cost_min: costMin ? parseFloat(costMin) : undefined,
      cost_max: costMax ? parseFloat(costMax) : undefined,
      limit: 50,
    });
  };

  const resetFilters = () => {
    setDateFrom("");
    setDateTo("");
    setTechnicianFilter("");
    setCostMin("");
    setCostMax("");
    setFilters({ asset_id: assetId, limit: 50 });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return CheckCircle;
      case "in_progress":
        return Clock;
      case "scheduled":
        return Calendar;
      default:
        return AlertCircle;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-600 bg-green-100";
      case "in_progress":
        return "text-blue-600 bg-blue-100";
      case "scheduled":
        return "text-amber-600 bg-amber-100";
      default:
        return "text-slate-500 bg-slate-100";
    }
  };

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <div className="bg-slate-50 rounded-lg p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Date From</label>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Date To</label>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Technician</label>
            <Input
              type="text"
              value={technicianFilter}
              onChange={(e) => setTechnicianFilter(e.target.value)}
              placeholder="Filter by technician"
              className="w-full"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Cost Range</label>
            <div className="flex gap-2">
              <Input
                type="number"
                value={costMin}
                onChange={(e) => setCostMin(e.target.value)}
                placeholder="Min"
                className="w-full"
              />
              <Input
                type="number"
                value={costMax}
                onChange={(e) => setCostMax(e.target.value)}
                placeholder="Max"
                className="w-full"
              />
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={applyFilters}>Search</Button>
          <Button variant="outline" onClick={resetFilters}>Reset</Button>
        </div>
      </div>

      {/* Timeline View */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : maintenanceHistory && maintenanceHistory.length > 0 ? (
        <div className="relative border-l-2 border-slate-200 ml-3 space-y-6 py-2">
          {maintenanceHistory.map((record) => {
            const StatusIcon = getStatusIcon(record.status);
            const statusColor = getStatusColor(record.status);

            return (
              <div key={record.id} className="relative pl-6">
                <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full border-2 border-white ${statusColor.split(' ')[1]}`}></div>
                <div className="bg-white rounded-lg border border-slate-100 p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => {
                    setSelectedRecord(record);
                    setShowDetails(true);
                  }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${statusColor} flex items-center gap-1`}>
                      <StatusIcon size={12} />
                      {record.status}
                    </span>
                    <span className="text-xs text-slate-400">
                      {format(new Date(record.scheduled_date), "dd/MM/yyyy")}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-800 mb-2">{record.title}</p>
                  <p className="text-sm text-slate-600 mb-2 line-clamp-2">{record.description}</p>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    {record.technician && (
                      <span className="flex items-center gap-1">
                        <User size={12} />
                        {record.technician}
                      </span>
                    )}
                    {(record.actual_cost || record.estimated_cost) && (
                      <span className="flex items-center gap-1">
                        <DollarSign size={12} />
                        {record.actual_cost
                          ? `$${record.actual_cost.toLocaleString()}`
                          : `~$${record.estimated_cost?.toLocaleString()}`}
                      </span>
                    )}
                    {record.approval_status && (
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        record.approval_status === "approved" ? "bg-green-100 text-green-700" :
                        record.approval_status === "rejected" ? "bg-red-100 text-red-700" :
                        "bg-yellow-100 text-yellow-700"
                      }`}>
                        {record.approval_status}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>No maintenance history found.</p>
        </div>
      )}

      {/* Details Panel */}
      {selectedRecord && (
        <Dialog open={showDetails} onOpenChange={setShowDetails}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{selectedRecord.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Full Description</label>
                <p className="text-sm text-slate-900 mt-1">{selectedRecord.description}</p>
              </div>
              {selectedRecord.notes && (
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Notes</label>
                  <p className="text-sm text-slate-900 mt-1">{selectedRecord.notes}</p>
                </div>
              )}
              {selectedRecord.parts_replaced && selectedRecord.parts_replaced.length > 0 && (
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Parts Replaced</label>
                  <ul className="list-disc list-inside text-sm text-slate-900 mt-1">
                    {selectedRecord.parts_replaced.map((part, idx) => (
                      <li key={idx}>{part}</li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedRecord.attachments && selectedRecord.attachments.length > 0 && (
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Attachments</label>
                  <div className="space-y-2 mt-2">
                    {selectedRecord.attachments.map((attachment, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-slate-50 p-2 rounded">
                        <span className="text-sm text-slate-900">{attachment.file_name}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(attachment.file_url, "_blank")}
                        >
                          <Download size={14} />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Status</label>
                  <p className="text-sm text-slate-900 mt-1">{selectedRecord.status}</p>
                </div>
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Priority</label>
                  <p className="text-sm text-slate-900 mt-1">{selectedRecord.priority}</p>
                </div>
                {selectedRecord.technician && (
                  <div>
                    <label className="text-xs text-slate-500 uppercase tracking-wide">Technician</label>
                    <p className="text-sm text-slate-900 mt-1">{selectedRecord.technician}</p>
                  </div>
                )}
                {(selectedRecord.actual_cost || selectedRecord.estimated_cost) && (
                  <div>
                    <label className="text-xs text-slate-500 uppercase tracking-wide">Cost</label>
                    <p className="text-sm text-slate-900 mt-1">
                      {selectedRecord.actual_cost
                        ? `$${selectedRecord.actual_cost.toLocaleString()}`
                        : `~$${selectedRecord.estimated_cost?.toLocaleString()}`}
                    </p>
                  </div>
                )}
              </div>
              {selectedRecord.approval_status === "pending" && (
                <MaintenanceApproval
                  maintenanceId={selectedRecord.id}
                  onApproved={() => {
                    queryClient.invalidateQueries({ queryKey: ["maintenance"] });
                    setShowDetails(false);
                  }}
                />
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default MaintenanceHistoryTab;
