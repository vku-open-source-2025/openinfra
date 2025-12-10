import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { preventiveMaintenanceApi } from "../../api/preventive-maintenance";
import { format } from "date-fns";
import { Skeleton } from "../ui/skeleton";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Edit, Calendar, AlertTriangle, CheckCircle } from "lucide-react";
import CalendarView from "../CalendarView";
import { isMaintenanceOverdue, isMaintenanceDueSoon } from "../../utils/healthScore";
import type { PreventiveMaintenancePlanUpdateRequest } from "../../types/preventive-maintenance";

interface PreventiveMaintenanceTabProps {
  assetId: string;
}

const PreventiveMaintenanceTab: React.FC<PreventiveMaintenanceTabProps> = ({ assetId }) => {
  const queryClient = useQueryClient();
  const [showEditModal, setShowEditModal] = useState(false);
  const [cycleDays, setCycleDays] = useState("");
  const [cycleDescription, setCycleDescription] = useState("");
  const [warningDays, setWarningDays] = useState("7");
  const [responsibleTeam, setResponsibleTeam] = useState("");

  const { data: plan, isLoading } = useQuery({
    queryKey: ["preventive-maintenance", assetId],
    queryFn: () => preventiveMaintenanceApi.getPlan(assetId),
  });

  const { data: upcomingTasks } = useQuery({
    queryKey: ["preventive-maintenance", "tasks", assetId],
    queryFn: () => preventiveMaintenanceApi.getUpcomingTasks(assetId),
    enabled: !!plan,
  });

  const { data: overdueTasks } = useQuery({
    queryKey: ["preventive-maintenance", "overdue", assetId],
    queryFn: () => preventiveMaintenanceApi.getOverdueTasks(assetId),
    enabled: !!plan,
  });

  const updateMutation = useMutation({
    mutationFn: (data: PreventiveMaintenancePlanUpdateRequest) =>
      plan ? preventiveMaintenanceApi.updatePlan(plan.id, data) : preventiveMaintenanceApi.createPlan({
        asset_id: assetId,
        cycle_days: parseInt(cycleDays),
        cycle_description: cycleDescription,
        warning_days: parseInt(warningDays),
        responsible_team: responsibleTeam,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preventive-maintenance", assetId] });
      setShowEditModal(false);
    },
  });

  const handleEdit = () => {
    if (plan) {
      setCycleDays(plan.cycle_days.toString());
      setCycleDescription(plan.cycle_description || "");
      setWarningDays(plan.warning_days?.toString() || "7");
      setResponsibleTeam(plan.responsible_team || "");
    }
    setShowEditModal(true);
  };

  const handleSave = () => {
    updateMutation.mutate({
      cycle_days: cycleDays ? parseInt(cycleDays) : undefined,
      cycle_description: cycleDescription || undefined,
      warning_days: warningDays ? parseInt(warningDays) : undefined,
      responsible_team: responsibleTeam || undefined,
    });
  };

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  return (
    <div className="space-y-6">
      {/* Current Plan Summary */}
      {plan ? (
        <div className="bg-slate-50 rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Tóm tắt kế hoạch hiện tại</h3>
              <Button variant="outline" size="sm" onClick={handleEdit}>
              <Edit className="h-4 w-4 mr-2" />
              Chỉnh sửa kế hoạch
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Chu kỳ</label>
              <p className="text-sm font-medium text-slate-900 mt-1">
                {plan.cycle_description || `Mỗi ${plan.cycle_days} ngày`}
              </p>
            </div>
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Bảo trì gần nhất</label>
              <p className="text-sm font-medium text-slate-900 mt-1">
                {plan.last_maintenance_date
                  ? format(new Date(plan.last_maintenance_date), "dd/MM/yyyy")
                  : "N/A"}
              </p>
            </div>
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide">Bảo trì tiếp theo</label>
              <p className="text-sm font-medium text-slate-900 mt-1">
                {format(new Date(plan.next_maintenance_date), "dd/MM/yyyy")}
              </p>
            </div>
            {plan.responsible_team && (
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Responsible Team</label>
                <p className="text-sm font-medium text-slate-900 mt-1">{plan.responsible_team}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-slate-50 rounded-lg p-6 text-center">
          <p className="text-slate-600 mb-4">Chưa có kế hoạch bảo trì định kỳ.</p>
          <Button onClick={() => setShowEditModal(true)}>
            Tạo kế hoạch bảo trì định kỳ
          </Button>
        </div>
      )}

      {/* Upcoming Tasks */}
      {upcomingTasks && upcomingTasks.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Công việc sắp tới</h3>
          <div className="space-y-2">
            {upcomingTasks.map((task) => {
              const isOverdue = isMaintenanceOverdue(task.scheduled_date);
              const isDueSoon = isMaintenanceDueSoon(task.scheduled_date, plan?.warning_days || 7);

              return (
                <div
                  key={task.id}
                  className={`bg-white border rounded-lg p-4 ${
                    isOverdue
                      ? "border-red-300 bg-red-50"
                      : isDueSoon
                      ? "border-yellow-300 bg-yellow-50"
                      : "border-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Calendar className={`${
                        isOverdue ? "text-red-600" : isDueSoon ? "text-yellow-600" : "text-slate-400"
                      }`} size={20} />
                      <div>
                        <p className="font-medium text-slate-900">
                          Due: {format(new Date(task.scheduled_date), "dd/MM/yyyy")}
                        </p>
                          <p className="text-sm text-slate-600">
                          Trạng thái: {task.status.replace("_", " ")}
                        </p>
                      </div>
                    </div>
                      {isOverdue && (
                      <span className="px-2 py-1 text-xs font-bold rounded bg-red-100 text-red-700">
                        QUÁ HẠN
                      </span>
                    )}
                    {isDueSoon && !isOverdue && (
                      <span className="px-2 py-1 text-xs font-bold rounded bg-yellow-100 text-yellow-700">
                        SẮP ĐẾN
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Overdue Tasks */}
      {overdueTasks && overdueTasks.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="text-red-600" size={20} />
            Overdue Tasks
          </h3>
          <div className="space-y-2">
            {overdueTasks.map((task) => (
              <div
                key={task.id}
                className="bg-red-50 border border-red-300 rounded-lg p-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="text-red-600" size={20} />
                    <div>
                      <p className="font-medium text-red-900">
                        Due: {format(new Date(task.scheduled_date), "dd/MM/yyyy")}
                      </p>
                      <p className="text-sm text-red-700">
                        Overdue by {Math.ceil((new Date().getTime() - new Date(task.scheduled_date).getTime()) / (1000 * 60 * 60 * 24))} days
                      </p>
                    </div>
                  </div>
                  <span className="px-2 py-1 text-xs font-bold rounded bg-red-200 text-red-900">
                    OVERDUE
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Calendar View */}
      {plan && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Maintenance Calendar</h3>
          <CalendarView logs={upcomingTasks?.map(task => ({
            _id: task.id,
            scheduled_date: task.scheduled_date,
            description: `Preventive maintenance`,
            status: task.status === "overdue" ? "Pending" : "Scheduled",
            technician: plan.responsible_team || "Team",
          })) || []} />
        </div>
      )}

      {/* Edit Plan Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{plan ? "Edit Plan" : "Create Preventive Maintenance Plan"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide mb-1 block">
                Maintenance Cycle (days)
              </label>
              <Input
                type="number"
                value={cycleDays}
                onChange={(e) => setCycleDays(e.target.value)}
                placeholder="ví dụ: 180 cho 6 tháng"
                min="1"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide mb-1 block">
                Cycle Description (optional)
              </label>
              <Input
                type="text"
                value={cycleDescription}
                onChange={(e) => setCycleDescription(e.target.value)}
                placeholder="ví dụ: Mỗi 6 tháng"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide mb-1 block">
                Warning Days
              </label>
              <Input
                type="number"
                value={warningDays}
                onChange={(e) => setWarningDays(e.target.value)}
                placeholder="Days before due date to show warning"
                min="1"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wide mb-1 block">
                Responsible Team (optional)
              </label>
              <Input
                type="text"
                value={responsibleTeam}
                onChange={(e) => setResponsibleTeam(e.target.value)}
                placeholder="Team name"
              />
            </div>
            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowEditModal(false)}
                disabled={updateMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={!cycleDays || updateMutation.isPending}
              >
                {updateMutation.isPending ? "Saving..." : plan ? "Update Plan" : "Create Plan"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PreventiveMaintenanceTab;
