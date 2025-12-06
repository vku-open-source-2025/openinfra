import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { incidentsApi } from "../../api/incidents";
import { format } from "date-fns";
import { Skeleton } from "../ui/skeleton";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Select } from "../ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { AlertTriangle, Plus, CheckCircle, Clock, XCircle } from "lucide-react";
import type { Incident } from "../../types/incident";

interface AssetIncidentsTabProps {
  assetId: string;
}

const AssetIncidentsTab: React.FC<AssetIncidentsTabProps> = ({ assetId }) => {
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const { data: incidents, isLoading } = useQuery({
    queryKey: ["incidents", assetId, statusFilter, severityFilter],
    queryFn: () =>
      incidentsApi.list({
        asset_id: assetId,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      }),
  });

  const filteredIncidents = incidents?.filter((incident) => {
    if (dateFrom && new Date(incident.created_at) < new Date(dateFrom)) return false;
    if (dateTo && new Date(incident.created_at) > new Date(dateTo)) return false;
    return true;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-100 text-red-700 border-red-300";
      case "high":
        return "bg-orange-100 text-orange-700 border-orange-300";
      case "medium":
        return "bg-yellow-100 text-yellow-700 border-yellow-300";
      default:
        return "bg-blue-100 text-blue-700 border-blue-300";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "closed":
        return CheckCircle;
      case "resolved":
        return CheckCircle;
      case "in_progress":
        return Clock;
      default:
        return AlertTriangle;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "closed":
      case "resolved":
        return "text-green-600 bg-green-100";
      case "in_progress":
        return "text-blue-600 bg-blue-100";
      default:
        return "text-amber-600 bg-amber-100";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Actions */}
      <div className="flex items-center justify-between">
        <Button
          onClick={() => {
            // TODO: Navigate to incident create with asset_id
            console.log("Create incident for asset:", assetId);
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          Report New Incident
        </Button>
      </div>

      {/* Filter Panel */}
      <div className="bg-slate-50 rounded-lg p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Status</label>
            <Select
              value={statusFilter}
              onValueChange={setStatusFilter}
            >
              <option value="">All Statuses</option>
              <option value="reported">Reported</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </Select>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Severity</label>
            <Select
              value={severityFilter}
              onValueChange={setSeverityFilter}
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </Select>
          </div>
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
        </div>
      </div>

      {/* Incident List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : filteredIncidents && filteredIncidents.length > 0 ? (
        <div className="space-y-3">
          {filteredIncidents.map((incident) => {
            const StatusIcon = getStatusIcon(incident.status);
            const statusColor = getStatusColor(incident.status);

            return (
              <div
                key={incident.id}
                className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => {
                  setSelectedIncident(incident);
                  setShowDetails(true);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className={`w-3 h-3 rounded-full mt-2 ${
                      incident.severity === "critical" ? "bg-red-500" :
                      incident.severity === "high" ? "bg-orange-500" :
                      incident.severity === "medium" ? "bg-yellow-500" :
                      "bg-blue-500"
                    }`} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-slate-900">{incident.title}</h4>
                        <span className={`px-2 py-0.5 text-xs font-bold rounded border ${getSeverityColor(incident.severity)}`}>
                          {incident.severity.toUpperCase()}
                        </span>
                        <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${statusColor} flex items-center gap-1`}>
                          <StatusIcon size={12} />
                          {incident.status.replace("_", " ")}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 mb-2 line-clamp-2">{incident.description}</p>
                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        <span>Date: {format(new Date(incident.created_at), "dd/MM/yyyy")}</span>
                        <span>Reporter: {incident.reporter_type}</span>
                        {incident.assigned_to && <span>Assigned: {incident.assigned_to}</span>}
                        {incident.upvotes > 0 && <span>Upvotes: {incident.upvotes}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>No incidents found.</p>
        </div>
      )}

      {/* Incident Details Panel */}
      {selectedIncident && (
        <Dialog open={showDetails} onOpenChange={setShowDetails}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {selectedIncident.title}
                <span className={`px-2 py-1 text-xs font-bold rounded border ${getSeverityColor(selectedIncident.severity)}`}>
                  {selectedIncident.severity.toUpperCase()}
                </span>
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Description</label>
                <p className="text-sm text-slate-900 mt-1">{selectedIncident.description}</p>
              </div>

              {/* Status Workflow Bar */}
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide mb-2 block">Status Workflow</label>
                <div className="flex items-center gap-2">
                  {["reported", "acknowledged", "assigned", "in_progress", "resolved", "closed"].map((status, idx) => {
                    const isActive = selectedIncident.status === status;
                    const isCompleted = ["reported", "acknowledged", "assigned", "in_progress", "resolved", "closed"].indexOf(selectedIncident.status) >= idx;
                    return (
                      <div key={status} className="flex items-center">
                        <div className={`flex flex-col items-center ${isCompleted ? "text-green-600" : "text-slate-400"}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                            isActive ? "border-blue-600 bg-blue-50" :
                            isCompleted ? "border-green-600 bg-green-50" :
                            "border-slate-300 bg-slate-50"
                          }`}>
                            {isCompleted ? <CheckCircle size={16} /> : <div className="w-2 h-2 rounded-full bg-current" />}
                          </div>
                          <span className="text-xs mt-1 capitalize">{status.replace("_", " ")}</span>
                        </div>
                        {idx < 5 && (
                          <div className={`w-12 h-0.5 mx-1 ${isCompleted ? "bg-green-600" : "bg-slate-300"}`} />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Status</label>
                  <p className="text-sm text-slate-900 mt-1 capitalize">{selectedIncident.status.replace("_", " ")}</p>
                </div>
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Severity</label>
                  <p className="text-sm text-slate-900 mt-1 capitalize">{selectedIncident.severity}</p>
                </div>
                {selectedIncident.assigned_to && (
                  <div>
                    <label className="text-xs text-slate-500 uppercase tracking-wide">Assigned Technician</label>
                    <p className="text-sm text-slate-900 mt-1">{selectedIncident.assigned_to}</p>
                  </div>
                )}
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Reporter</label>
                  <p className="text-sm text-slate-900 mt-1 capitalize">{selectedIncident.reporter_type}</p>
                </div>
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Created</label>
                  <p className="text-sm text-slate-900 mt-1">{format(new Date(selectedIncident.created_at), "dd/MM/yyyy HH:mm")}</p>
                </div>
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide">Updated</label>
                  <p className="text-sm text-slate-900 mt-1">{format(new Date(selectedIncident.updated_at), "dd/MM/yyyy HH:mm")}</p>
                </div>
              </div>

              {/* Activity Log / Comments */}
              {selectedIncident.comments && selectedIncident.comments.length > 0 && (
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wide mb-2 block">Activity Log</label>
                  <div className="space-y-2">
                    {selectedIncident.comments.map((comment, idx) => {
                      const dateStr = comment.posted_at || comment.created_at;
                      const date = dateStr ? new Date(dateStr) : null;
                      const formattedDate = date && !isNaN(date.getTime()) 
                        ? format(date, "dd/MM/yyyy HH:mm") 
                        : "Unknown";
                      return (
                        <div key={idx} className="bg-slate-50 p-3 rounded">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-slate-900">
                              {comment.user_name || "System"}
                            </span>
                            <span className="text-xs text-slate-500">
                              {formattedDate}
                            </span>
                          </div>
                          <p className="text-sm text-slate-700">{comment.comment}</p>
                          {comment.is_internal && (
                            <span className="text-xs text-amber-600 mt-1 inline-block">Internal Note</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-slate-200">
                <Button
                  variant="outline"
                  onClick={() => {
                    // TODO: Navigate to change status
                    console.log("Change status for incident:", selectedIncident.id);
                  }}
                >
                  Change Status
                </Button>
                <Button
                  onClick={() => {
                    // TODO: Create maintenance from incident
                    console.log("Create maintenance from incident:", selectedIncident.id);
                  }}
                >
                  Create Maintenance from Incident
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default AssetIncidentsTab;
