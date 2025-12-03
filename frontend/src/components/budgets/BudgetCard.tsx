import type { Budget } from "../../types/budget"
import { Badge } from "../ui/badge"
import { DollarSign, Calendar } from "lucide-react"
import { format } from "date-fns"

interface BudgetCardProps {
  budget: Budget
  onClick?: () => void
}

export const BudgetCard: React.FC<BudgetCardProps> = ({ budget, onClick }) => {
  // Safely handle undefined/null values with defaults
  const totalAmount = budget.total_amount ?? 0
  const spentAmount = budget.spent_amount ?? 0
  const allocatedAmount = budget.allocated_amount ?? 0

  const utilizationPercent = totalAmount > 0
    ? (spentAmount / totalAmount) * 100
    : 0

  const statusConfig: Record<typeof budget.status, { label: string; variant: "default" | "secondary" | "success" | "destructive" | "outline" }> = {
    draft: { label: "Draft", variant: "outline" },
    submitted: { label: "Submitted", variant: "secondary" },
    approved: { label: "Approved", variant: "success" },
    rejected: { label: "Rejected", variant: "destructive" },
  }

  const statusInfo = statusConfig[budget.status]

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-lg border p-4 hover:shadow-md transition-shadow ${
        onClick ? "cursor-pointer" : ""
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900 mb-1">{budget.budget_code}</h3>
          <p className="text-sm text-slate-600 mb-2">{budget.category}</p>
        </div>
        <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
      </div>

      <div className="space-y-2 mb-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Total Budget</span>
          <span className="font-semibold text-slate-900">
            {totalAmount.toLocaleString()} VND
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Spent</span>
          <span className="font-semibold text-red-600">
            {spentAmount.toLocaleString()} VND
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Remaining</span>
          <span className="font-semibold text-green-600">
            {(totalAmount - spentAmount).toLocaleString()} VND
          </span>
        </div>
      </div>

      <div className="mb-2">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span>Utilization</span>
          <span>{utilizationPercent.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              utilizationPercent > 90 ? "bg-red-600" :
              utilizationPercent > 75 ? "bg-amber-600" :
              "bg-green-600"
            }`}
            style={{ width: `${Math.min(utilizationPercent, 100)}%` }}
          />
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs text-slate-500 mt-3">
        <div className="flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          <span>FY {budget.fiscal_year}</span>
        </div>
        <div className="flex items-center gap-1">
          <DollarSign className="h-3 w-3" />
          <span>{allocatedAmount.toLocaleString()} allocated</span>
        </div>
      </div>
    </div>
  )
}
