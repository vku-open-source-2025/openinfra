import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { usersApi } from "../../api/users"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table"
import { Badge } from "../../components/ui/badge"
import { Select } from "../../components/ui/select"
import { Input } from "../../components/ui/input"
import { Button } from "../../components/ui/button"
import { Pagination } from "../../components/ui/pagination"
import { Skeleton } from "../../components/ui/skeleton"
import { Plus, Edit, Trash2 } from "lucide-react"
import { useAuthStore } from "../../stores/authStore"
import type { UserRole, UserStatus } from "../../types/user"

const UserList: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuthStore()
  const [page, setPage] = useState(1)
  const [role, setRole] = useState<string>("")
  const [status, setStatus] = useState<string>("")
  const [search, setSearch] = useState<string>("")
  const limit = 20

  const { data: users, isLoading } = useQuery({
    queryKey: ["users", page, role, status],
    queryFn: () =>
      usersApi.list({
        skip: (page - 1) * limit,
        limit,
        role: role || undefined,
        status: status || undefined,
      }),
    enabled: currentUser?.role === "admin",
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => usersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const filteredUsers = users?.filter((user) => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      user.username.toLowerCase().includes(searchLower) ||
      user.email.toLowerCase().includes(searchLower) ||
      user.full_name.toLowerCase().includes(searchLower)
    )
  })

  const totalPages = users ? Math.ceil(users.length / limit) : 1

  if (currentUser?.role !== "admin") {
    return (
      <div className="p-6 text-center text-red-500">
        Từ chối truy cập. Cần quyền quản trị.
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Quản lý người dùng</h1>
          <p className="text-slate-500 mt-1">Quản lý người dùng và phân quyền hệ thống</p>
        </div>
        <Button onClick={() => navigate({ to: "/admin/users/create" })}>
          <Plus className="h-4 w-4 mr-2" />
          Tạo người dùng
        </Button>
      </div>

      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <Input
            placeholder="Tìm kiếm người dùng..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="Tất cả vai trò"
        >
          <option value="">Tất cả vai trò</option>
          <option value="admin">Quản trị</option>
          <option value="manager">Quản lý</option>
          <option value="technician">Kỹ thuật</option>
          <option value="citizen">Người dân</option>
        </Select>
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="Tất cả trạng thái"
        >
          <option value="">Tất cả trạng thái</option>
          <option value="active">Đang hoạt động</option>
          <option value="inactive">Ngưng hoạt động</option>
          <option value="suspended">Tạm khóa</option>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : filteredUsers && filteredUsers.length > 0 ? (
        <>
          <div className="bg-white rounded-lg border border-slate-200">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tên đăng nhập</TableHead>
                  <TableHead>Họ tên</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Vai trò</TableHead>
                  <TableHead>Trạng thái</TableHead>
                  <TableHead className="text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.username}</TableCell>
                    <TableCell>{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="capitalize">
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          user.status === "active"
                            ? "success"
                            : user.status === "suspended"
                            ? "destructive"
                            : "outline"
                        }
                        className="capitalize"
                      >
                        {user.status === "active"
                          ? "Đang hoạt động"
                          : user.status === "suspended"
                          ? "Tạm khóa"
                          : "Ngưng hoạt động"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate({ to: `/admin/users/${user.id}` })}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        {user.id !== currentUser?.id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (confirm(`Bạn chắc chắn muốn xóa ${user.username}?`)) {
                                deleteMutation.mutate(user.id)
                              }
                            }}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {totalPages > 1 && (
            <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
          )}
        </>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>Không tìm thấy người dùng.</p>
        </div>
      )}
    </div>
  )
}

export default UserList
