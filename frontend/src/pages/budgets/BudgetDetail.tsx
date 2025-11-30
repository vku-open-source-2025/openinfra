import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useNavigate } from "@tanstack/react-router"
import { budgetsApi } from "../../api/budgets"
import { BudgetProgress } from "../../components/budgets/BudgetProgress"
import { TransactionList } from "../../components/budgets/TransactionList"
import { TransactionForm } from "../../components/budgets/TransactionForm"
import { ApprovalWorkflow } from "../../components/budgets/ApprovalWorkflow"
import { Button } from "../../components/ui/button"
import { Skeleton } from "../../components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog"
import { ArrowLeft, Plus } from "lucide-react"
import { useAuthStore } from "../../stores/authStore"
import type { BudgetTransactionCreateRequest } from "../../types/budget"

const BudgetDetail: React.FC = () => {
  const { id } = useParams({ from: "/admin/budgets/$id" })
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const [showTransactionForm, setShowTransactionForm] = useState(false)

  const { data: budget, isLoading } = useQuery({
    queryKey: ["budget", id],
    queryFn: () => budgetsApi.getById(id),
  })

  const { data: transactions } = useQuery({
    queryKey: ["budget-transactions", id],
    queryFn: () => budgetsApi.getTransactions(id),
    enabled: !!budget,
  })

  const submitMutation = useMutation({
    mutationFn: () => budgetsApi.submit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget", id] })
      queryClient.invalidateQueries({ queryKey: ["budgets"] })
    },
  })

  const approveMutation = useMutation({
    mutationFn: () => budgetsApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget", id] })
      queryClient.invalidateQueries({ queryKey: ["budgets"] })
    },
  })

  const createTransactionMutation = useMutation({
    mutationFn: (data: BudgetTransactionCreateRequest) => budgetsApi.createTransaction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget", id] })
      queryClient.invalidateQueries({ queryKey: ["budget-transactions", id] })
      setShowTransactionForm(false)
    },
  })

  const approveTransactionMutation = useMutation({
    mutationFn: (transactionId: string) => budgetsApi.approveTransaction(transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget-transactions", id] })
      queryClient.invalidateQueries({ queryKey: ["budget", id] })
    },
  })

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!budget) {
    return (
      <div className="p-6 text-center text-red-500">
        Budget not found.
      </div>
    )
  }

  const canManage = user?.role === "admin" || user?.role === "manager"
  const canSubmit = canManage && budget.status === "draft"
  const canApprove = canManage && budget.status === "submitted"

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/budgets" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Budgets
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">{budget.budget_code}</h1>
            <p className="text-slate-600">{budget.category} - Fiscal Year {budget.fiscal_year}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-1">Total Budget</h3>
            <p className="text-2xl font-bold text-slate-900">{budget.total_amount.toLocaleString()} VND</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-1">Spent</h3>
            <p className="text-2xl font-bold text-red-600">{budget.spent_amount.toLocaleString()} VND</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-1">Remaining</h3>
            <p className="text-2xl font-bold text-green-600">
              {(budget.total_amount - budget.spent_amount).toLocaleString()} VND
            </p>
          </div>
        </div>

        <BudgetProgress budget={budget} />

        {canManage && (
          <div className="mt-6 pt-6 border-t">
            <ApprovalWorkflow
              budget={budget}
              onSubmit={async () => {
                await submitMutation.mutateAsync()
              }}
              onApprove={async () => {
                await approveMutation.mutateAsync()
              }}
              canSubmit={canSubmit}
              canApprove={canApprove}
              isProcessing={submitMutation.isPending || approveMutation.isPending}
            />
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Transactions</h2>
          {canManage && budget.status === "approved" && (
            <Button onClick={() => setShowTransactionForm(true)} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Transaction
            </Button>
          )}
        </div>

        {transactions && transactions.length > 0 ? (
          <TransactionList transactions={transactions} />
        ) : (
          <div className="text-center py-8 text-slate-500">
            <p>No transactions yet</p>
          </div>
        )}
      </div>

      <Dialog open={showTransactionForm} onOpenChange={setShowTransactionForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Transaction</DialogTitle>
          </DialogHeader>
          <TransactionForm
            onSubmit={async (data) => {
              await createTransactionMutation.mutateAsync(data)
            }}
            onCancel={() => setShowTransactionForm(false)}
            isLoading={createTransactionMutation.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default BudgetDetail
