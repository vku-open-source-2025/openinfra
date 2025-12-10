import type { BudgetTransaction } from "../../types/budget"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import { Badge } from "../ui/badge"
import { format } from "date-fns"
import { ArrowUp, ArrowDown } from "lucide-react"

interface TransactionListProps {
  transactions: BudgetTransaction[]
}

export const TransactionList: React.FC<TransactionListProps> = ({ transactions }) => {
  if (transactions.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>Không tìm thấy giao dịch</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Ngày</TableHead>
          <TableHead>Mô tả</TableHead>
          <TableHead>Loại</TableHead>
          <TableHead className="text-right">Số tiền</TableHead>
          <TableHead>Trạng thái</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transactions.map((transaction) => (
          <TableRow key={transaction.id}>
            <TableCell className="text-sm">
              {format(new Date(transaction.created_at), "MMM d, yyyy")}
            </TableCell>
            <TableCell className="text-sm">{transaction.description}</TableCell>
            <TableCell>
              {transaction.transaction_type === "expense" ? (
                <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                  <ArrowDown className="h-3 w-3" />
                  Chi tiêu
                </Badge>
              ) : (
                <Badge variant="success" className="flex items-center gap-1 w-fit">
                  <ArrowUp className="h-3 w-3" />
                  Phân bổ
                </Badge>
              )}
            </TableCell>
            <TableCell className="text-right font-semibold">
              {transaction.amount.toLocaleString()} VND
            </TableCell>
            <TableCell>
              {transaction.approved_at ? (
                <Badge variant="success">Đã duyệt</Badge>
              ) : (
                <Badge variant="outline">Đang chờ</Badge>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
