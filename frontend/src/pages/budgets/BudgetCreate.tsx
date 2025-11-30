import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { budgetsApi } from "../../api/budgets"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Textarea } from "../../components/ui/textarea"
import { Button } from "../../components/ui/button"
import { ArrowLeft } from "lucide-react"
import type { BudgetCreateRequest } from "../../types/budget"

const BudgetCreate: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<Partial<BudgetCreateRequest>>({
    fiscal_year: new Date().getFullYear(),
    category: "",
    total_amount: 0,
    breakdown: {},
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const createMutation = useMutation({
    mutationFn: (data: BudgetCreateRequest) => budgetsApi.create(data),
    onSuccess: (budget) => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] })
      navigate({ to: `/admin/budgets/${budget.id}` })
    },
    onError: (error: any) => {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!formData.fiscal_year) {
      setErrors({ fiscal_year: "Fiscal year is required" })
      return
    }
    if (!formData.category?.trim()) {
      setErrors({ category: "Category is required" })
      return
    }
    if (!formData.total_amount || formData.total_amount <= 0) {
      setErrors({ total_amount: "Total amount must be greater than 0" })
      return
    }

    createMutation.mutate(formData as BudgetCreateRequest)
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/budgets" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Budgets
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Create New Budget</h1>

        <Form onSubmit={handleSubmit}>
          <FormField>
            <FormLabel required>Fiscal Year</FormLabel>
            <Input
              type="number"
              value={formData.fiscal_year || ""}
              onChange={(e) =>
                setFormData({ ...formData, fiscal_year: parseInt(e.target.value) || 0 })
              }
              placeholder={new Date().getFullYear().toString()}
            />
            {errors.fiscal_year && <FormError>{errors.fiscal_year}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Category</FormLabel>
            <Input
              value={formData.category || ""}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              placeholder="e.g., Maintenance, Infrastructure, Operations"
            />
            {errors.category && <FormError>{errors.category}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Total Amount (VND)</FormLabel>
            <Input
              type="number"
              step="0.01"
              value={formData.total_amount || ""}
              onChange={(e) =>
                setFormData({ ...formData, total_amount: parseFloat(e.target.value) || 0 })
              }
              placeholder="0.00"
            />
            {errors.total_amount && <FormError>{errors.total_amount}</FormError>}
          </FormField>

          {errors.submit && <FormError>{errors.submit}</FormError>}

          <div className="flex gap-4 mt-6">
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Budget"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate({ to: "/admin/budgets" })}
            >
              Cancel
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default BudgetCreate
