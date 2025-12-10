import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { usersApi } from "../../api/users"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import { ArrowLeft } from "lucide-react"
import { useAuthStore } from "../../stores/authStore"
import type { UserCreateRequest, UserRole } from "../../types/user"

const UserCreate: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuthStore()
  const [formData, setFormData] = useState<Partial<UserCreateRequest>>({
    username: "",
    email: "",
    password: "",
    full_name: "",
    phone: "",
    role: "citizen",
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const createMutation = useMutation({
    mutationFn: (data: UserCreateRequest) => usersApi.create(data),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      navigate({ to: `/admin/users/${user.id}` })
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

    if (!formData.username?.trim()) {
      setErrors({ username: "Tên đăng nhập là bắt buộc" })
      return
    }
    if (!formData.email?.trim()) {
      setErrors({ email: "Email là bắt buộc" })
      return
    }
    if (!formData.password || formData.password.length < 6) {
      setErrors({ password: "Mật khẩu tối thiểu 6 ký tự" })
      return
    }
    if (!formData.full_name?.trim()) {
      setErrors({ full_name: "Họ tên là bắt buộc" })
      return
    }

    createMutation.mutate(formData as UserCreateRequest)
  }

  if (currentUser?.role !== "admin") {
    return (
      <div className="p-6 text-center text-red-500">
        Từ chối truy cập. Cần quyền quản trị.
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
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Tạo người dùng mới</h1>

        <Form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField>
              <FormLabel required>Tên đăng nhập</FormLabel>
              <Input
                value={formData.username || ""}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="johndoe"
              />
              {errors.username && <FormError>{errors.username}</FormError>}
            </FormField>

            <FormField>
              <FormLabel required>Email</FormLabel>
              <Input
                type="email"
                value={formData.email || ""}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="john@example.com"
              />
              {errors.email && <FormError>{errors.email}</FormError>}
            </FormField>

            <FormField>
              <FormLabel required>Mật khẩu</FormLabel>
              <Input
                type="password"
                value={formData.password || ""}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="••••••••"
              />
              {errors.password && <FormError>{errors.password}</FormError>}
            </FormField>

            <FormField>
              <FormLabel required>Họ tên</FormLabel>
              <Input
                value={formData.full_name || ""}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="Nguyễn Văn A"
              />
              {errors.full_name && <FormError>{errors.full_name}</FormError>}
            </FormField>

            <FormField>
              <FormLabel>Số điện thoại</FormLabel>
              <Input
                value={formData.phone || ""}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+84 123 456 789"
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
          </div>

          {errors.submit && <FormError>{errors.submit}</FormError>}

          <div className="flex gap-4 mt-6">
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Đang tạo..." : "Tạo người dùng"}
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

export default UserCreate
