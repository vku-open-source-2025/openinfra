import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useNavigate } from "@tanstack/react-router"
import { usersApi } from "../../api/users"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import { Skeleton } from "../../components/ui/skeleton"
import { ArrowLeft } from "lucide-react"
import { useAuthStore } from "../../stores/authStore"
import type { UserUpdateRequest, UserRole, UserStatus } from "../../types/user"

const UserDetail: React.FC = () => {
  const { id } = useParams({ from: "/admin/users/$id" })
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuthStore()

  const { data: user, isLoading } = useQuery({
    queryKey: ["user", id],
    queryFn: () => usersApi.getById(id),
    enabled: currentUser?.role === "admin",
  })

  const updateMutation = useMutation({
    mutationFn: (data: UserUpdateRequest) => usersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", id] })
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const [formData, setFormData] = useState<Partial<UserUpdateRequest>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email,
        full_name: user.full_name,
        phone: user.phone,
        role: user.role,
        status: user.status,
        department: user.department,
      })
    }
  }, [user])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!formData.email?.trim()) {
      setErrors({ email: "Email là bắt buộc" })
      return
    }

    updateMutation.mutate(formData as UserUpdateRequest)
  }

  if (currentUser?.role !== "admin") {
    return (
      <div className="p-6 text-center text-red-500">
        Từ chối truy cập. Cần quyền quản trị.
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-6 text-center text-red-500">
        Không tìm thấy người dùng.
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/users" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Quay lại danh sách
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Chỉnh sửa người dùng</h1>

        <Form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField>
              <FormLabel>Tên đăng nhập</FormLabel>
              <Input value={user.username} disabled className="bg-slate-50" />
            </FormField>

            <FormField>
              <FormLabel required>Email</FormLabel>
              <Input
                type="email"
                value={formData.email || ""}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
              {errors.email && <FormError>{errors.email}</FormError>}
            </FormField>

            <FormField>
              <FormLabel required>Họ tên</FormLabel>
              <Input
                value={formData.full_name || ""}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
            </FormField>

            <FormField>
              <FormLabel>Số điện thoại</FormLabel>
              <Input
                value={formData.phone || ""}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </FormField>

            <FormField>
              <FormLabel required>Vai trò</FormLabel>
              <Select
                value={formData.role || "citizen"}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
              >
                <option value="admin">Quản trị</option>
                <option value="manager">Quản lý</option>
                <option value="technician">Kỹ thuật</option>
                <option value="citizen">Người dân</option>
              </Select>
            </FormField>

            <FormField>
              <FormLabel required>Trạng thái</FormLabel>
              <Select
                value={formData.status || "active"}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as UserStatus })}
              >
                <option value="active">Đang hoạt động</option>
                <option value="inactive">Ngưng hoạt động</option>
                <option value="suspended">Tạm khóa</option>
              </Select>
            </FormField>

            <FormField>
              <FormLabel>Phòng ban</FormLabel>
              <Input
                value={formData.department || ""}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              />
            </FormField>
          </div>

          <div className="flex gap-4 mt-6">
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Đang cập nhật..." : "Cập nhật"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate({ to: "/admin/users" })}
            >
              Hủy
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default UserDetail
