import type { Budget } from "../../types/budget"

interface BudgetProgressProps {
  budget: Budget
  showDetails?: boolean
}

export const BudgetProgress: React.FC<BudgetProgressProps> = ({ budget, showDetails = true }) => {
  const utilizationPercent = budget.total_amount > 0
    ? (budget.spent_amount / budget.total_amount) * 100
    : 0

  return (
    <div className="space-y-2">
      {showDetails && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Budget Utilization</span>
          <span className="font-semibold">{utilizationPercent.toFixed(1)}%</span>
        </div>
      )}
      <div className="w-full bg-slate-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all ${
            utilizationPercent > 90 ? "bg-red-600" :
            utilizationPercent > 75 ? "bg-amber-600" :
            "bg-green-600"
          }`}
          style={{ width: `${Math.min(utilizationPercent, 100)}%` }}
        />
      </div>
      {showDetails && (
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Spent: {budget.spent_amount.toLocaleString()} VND</span>
          <span>Remaining: {(budget.total_amount - budget.spent_amount).toLocaleString()} VND</span>
        </div>
      )}
    </div>
  )
}
