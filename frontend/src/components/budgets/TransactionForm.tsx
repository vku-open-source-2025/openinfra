import { useState } from "react"
import { Form, FormField, FormLabel, FormError } from "../ui/form"
import { Input } from "../ui/input"
import { Textarea } from "../ui/textarea"
import { Select } from "../ui/select"
import { Button } from "../ui/button"
import type { BudgetTransactionCreateRequest, TransactionType } from "../../types/budget"

interface TransactionFormProps {
  onSubmit: (data: BudgetTransactionCreateRequest) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

export const TransactionForm: React.FC<TransactionFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<Partial<BudgetTransactionCreateRequest>>({
    amount: 0,
    description: "",
    transaction_type: "expense",
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!formData.amount || formData.amount <= 0) {
      setErrors({ amount: "Số tiền phải lớn hơn 0" })
      return
    }
    if (!formData.description?.trim()) {
      setErrors({ description: "Mô tả là bắt buộc" })
      return
    }

    await onSubmit(formData as BudgetTransactionCreateRequest)
    setFormData({ amount: 0, description: "", transaction_type: "expense" })
  }

  return (
    <Form onSubmit={handleSubmit}>
      <FormField>
        <FormLabel required>Loại giao dịch</FormLabel>
        <Select
          value={formData.transaction_type || "expense"}
          onChange={(e) =>
            setFormData({ ...formData, transaction_type: e.target.value as TransactionType })
          }
        >
          <option value="expense">Chi phí</option>
          <option value="allocation">Phân bổ</option>
        </Select>
      </FormField>

      <FormField>
        <FormLabel required>Số tiền (VND)</FormLabel>
        <Input
          type="number"
          step="0.01"
          value={formData.amount || ""}
          onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
          placeholder="0.00"
        />
        {errors.amount && <FormError>{errors.amount}</FormError>}
      </FormField>

      <FormField>
        <FormLabel required>Mô tả</FormLabel>
        <Textarea
          value={formData.description || ""}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Mô tả giao dịch..."
          rows={3}
        />
        {errors.description && <FormError>{errors.description}</FormError>}
      </FormField>

      <div className="flex gap-4 mt-4">
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Đang thêm..." : "Thêm giao dịch"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Hủy
        </Button>
      </div>
    </Form>
  )
}
