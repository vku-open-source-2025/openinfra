import { Button } from "../ui/button"
import type { Budget } from "../../types/budget"
import { CheckCircle, X, Send } from "lucide-react"

interface ApprovalWorkflowProps {
  budget: Budget
  onSubmit: () => Promise<void>
  onApprove: () => Promise<void>
  onReject?: () => Promise<void>
  canSubmit?: boolean
  canApprove?: boolean
  canReject?: boolean
  isProcessing?: boolean
}

export const ApprovalWorkflow: React.FC<ApprovalWorkflowProps> = ({
  budget,
  onSubmit,
  onApprove,
  onReject,
  canSubmit = false,
  canApprove = false,
  canReject = false,
  isProcessing = false,
}) => {
  return (
    <div className="space-y-2">
      {budget.status === "draft" && canSubmit && (
        <Button onClick={onSubmit} disabled={isProcessing} className="w-full">
          <Send className="h-4 w-4 mr-2" />
          Submit for Approval
        </Button>
      )}

      {budget.status === "submitted" && canApprove && (
        <div className="flex gap-2">
          <Button onClick={onApprove} disabled={isProcessing} className="flex-1" variant="default">
            <CheckCircle className="h-4 w-4 mr-2" />
            Approve Budget
          </Button>
          {canReject && onReject && (
            <Button onClick={onReject} disabled={isProcessing} className="flex-1" variant="destructive">
              <X className="h-4 w-4 mr-2" />
              Reject
            </Button>
          )}
        </div>
      )}

      {budget.status === "approved" && (
        <div className="text-sm text-green-600 font-medium">
          Budget approved and active
        </div>
      )}

      {budget.status === "rejected" && (
        <div className="text-sm text-red-600 font-medium">
          Budget was rejected
        </div>
      )}
    </div>
  )
}
