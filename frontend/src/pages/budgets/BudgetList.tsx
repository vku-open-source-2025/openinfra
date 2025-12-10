import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { budgetsApi } from "../../api/budgets"
import { BudgetCard } from "../../components/budgets/BudgetCard"
import { Select } from "../../components/ui/select"
import { Input } from "../../components/ui/input"
import { Button } from "../../components/ui/button"
import { Pagination } from "../../components/ui/pagination"
import { Skeleton } from "../../components/ui/skeleton"
import { Plus } from "lucide-react"

const BudgetList: React.FC = () => {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [fiscalYear, setFiscalYear] = useState<string>("")
  const [status, setStatus] = useState<string>("")
  const [category, setCategory] = useState<string>("")
  const limit = 20

  const { data: budgets, isLoading } = useQuery({
    queryKey: ["budgets", page, fiscalYear, status, category],
    queryFn: () =>
      budgetsApi.list({
        skip: (page - 1) * limit,
        limit,
        fiscal_year: fiscalYear ? parseInt(fiscalYear) : undefined,
        status: status || undefined,
        category: category || undefined,
      }),
  })

  const totalPages = budgets ? Math.ceil(budgets.length / limit) : 1

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Ngân sách</h1>
          <p className="text-slate-500 mt-1">Quản lý kế hoạch và theo dõi ngân sách</p>
        </div>
        <Button onClick={() => navigate({ to: "/admin/budgets/create" })}>
          <Plus className="h-4 w-4 mr-2" />
          Tạo ngân sách
        </Button>
      </div>

      <div className="flex flex-wrap gap-4">
        <Input
          type="number"
          placeholder="Năm tài chính"
          value={fiscalYear}
          onChange={(e) => setFiscalYear(e.target.value)}
          className="w-[150px]"
        />
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="Tất cả trạng thái"
        >
          <option value="">All Statuses</option>
          <option value="draft">Bản nháp</option>
          <option value="submitted">Đã gửi</option>
          <option value="approved">Đã duyệt</option>
          <option value="rejected">Từ chối</option>
        </Select>
        <Input
          placeholder="Danh mục"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="flex-1 min-w-[200px]"
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-48 w-full" />
          ))}
        </div>
      ) : budgets && budgets.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {budgets.map((budget) => (
              <BudgetCard
                key={budget.id}
                budget={budget}
                onClick={() => navigate({ to: `/admin/budgets/${budget.id}` })}
              />
            ))}
          </div>
          {totalPages > 1 && (
            <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
          )}
        </>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>Không tìm thấy ngân sách.</p>
        </div>
      )}
    </div>
  )
}

export default BudgetList
