import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { maintenanceApi } from "../../api/maintenance";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";
import { CheckCircle, XCircle } from "lucide-react";

interface MaintenanceApprovalProps {
  maintenanceId: string;
  onApproved?: () => void;
}

const MaintenanceApproval: React.FC<MaintenanceApprovalProps> = ({ maintenanceId, onApproved }) => {
  const queryClient = useQueryClient();
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectForm, setShowRejectForm] = useState(false);

  const approveMutation = useMutation({
    mutationFn: () => maintenanceApi.approve(maintenanceId, { approval_status: "approved" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["maintenance"] });
      onApproved?.();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => maintenanceApi.reject(maintenanceId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["maintenance"] });
      setShowRejectForm(false);
      setRejectionReason("");
      onApproved?.();
    },
  });

  const handleApprove = () => {
    approveMutation.mutate();
  };

  const handleReject = () => {
    if (rejectionReason.trim()) {
      rejectMutation.mutate(rejectionReason);
    }
  };

  if (showRejectForm) {
    return (
      <div className="border-t border-slate-200 pt-4 mt-4">
        <h4 className="text-sm font-semibold text-slate-900 mb-2">Rejection Reason</h4>
        <Textarea
          value={rejectionReason}
          onChange={(e) => setRejectionReason(e.target.value)}
          placeholder="Enter reason for rejection..."
          className="mb-3"
          rows={3}
        />
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              setShowRejectForm(false);
              setRejectionReason("");
            }}
            disabled={approveMutation.isPending || rejectMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleReject}
            disabled={!rejectionReason.trim() || rejectMutation.isPending}
            className="bg-red-600 hover:bg-red-700"
          >
            {rejectMutation.isPending ? "Rejecting..." : "Confirm Rejection"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-slate-200 pt-4 mt-4">
      <h4 className="text-sm font-semibold text-slate-900 mb-3">Approve / Reject Maintenance Record</h4>
      <div className="flex gap-2">
        <Button
          onClick={handleApprove}
          disabled={approveMutation.isPending || rejectMutation.isPending}
          className="bg-green-600 hover:bg-green-700"
        >
          <CheckCircle className="h-4 w-4 mr-2" />
          {approveMutation.isPending ? "Approving..." : "Approve"}
        </Button>
        <Button
          variant="outline"
          onClick={() => setShowRejectForm(true)}
          disabled={approveMutation.isPending || rejectMutation.isPending}
          className="border-red-300 text-red-600 hover:bg-red-50"
        >
          <XCircle className="h-4 w-4 mr-2" />
          Reject
        </Button>
      </div>
    </div>
  );
};

export { MaintenanceApproval };
