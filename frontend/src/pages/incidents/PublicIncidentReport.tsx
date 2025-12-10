import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { publicApi } from "../../api/public"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Textarea } from "../../components/ui/textarea"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import { Turnstile } from "../../components/Turnstile"
import type { IncidentCreateRequest, IncidentSeverity } from "../../types/incident"

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || ""

const PublicIncidentReport: React.FC = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState<Partial<IncidentCreateRequest>>({
    title: "",
    description: "",
    severity: "medium",
    location: {
      address: "",
      coordinates: {
        longitude: 0,
        latitude: 0,
      },
    },
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [turnstileToken, setTurnstileToken] = useState<string>("")

  const createMutation = useMutation({
    mutationFn: (data: IncidentCreateRequest) => publicApi.createAnonymousIncident(data, turnstileToken),
    onSuccess: (incident) => {
      navigate({ to: `/public/incidents/${incident.id}` })
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

    if (!formData.title?.trim()) {
      setErrors({ title: "Title is required" })
      return
    }
    if (!formData.description?.trim()) {
      setErrors({ description: "Description is required" })
      return
    }
    if (!formData.location?.address?.trim()) {
      setErrors({ address: "Address is required" })
      return
    }
    if (TURNSTILE_SITE_KEY && !turnstileToken) {
      setErrors({ captcha: "Please complete the captcha verification" })
      return
    }

    createMutation.mutate(formData as IncidentCreateRequest)
  }

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Báo sự cố</h1>
        <p className="text-slate-600 mb-8">
          Hãy giúp chúng tôi cải thiện hạ tầng bằng cách báo các vấn đề bạn gặp phải.
        </p>

        <Form onSubmit={handleSubmit}>
          <FormField>
            <FormLabel required>Bạn gặp sự cố gì?</FormLabel>
            <Input
              value={formData.title || ""}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Mô tả ngắn (ví dụ: ổ gà trên đường chính)"
            />
            {errors.title && <FormError>{errors.title}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Chi tiết</FormLabel>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Mô tả chi tiết về sự cố..."
              rows={5}
            />
            {errors.description && <FormError>{errors.description}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Mức độ nghiêm trọng</FormLabel>
            <Select
              value={formData.severity || "medium"}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value as IncidentSeverity })}
            >
              <option value="low">Thấp - Vấn đề nhỏ</option>
              <option value="medium">Trung bình - Vấn đề vừa</option>
              <option value="high">Cao - Vấn đề nghiêm trọng</option>
              <option value="critical">Nguy kịch - Cần xử lý khẩn</option>
            </Select>
          </FormField>

          <FormField>
            <FormLabel required>Địa điểm</FormLabel>
            <Input
              value={formData.location?.address || ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  location: {
                    ...formData.location!,
                    address: e.target.value,
                  },
                })
              }
              placeholder="Địa chỉ hoặc mô tả vị trí"
            />
            {errors.address && <FormError>{errors.address}</FormError>}
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField>
              <FormLabel>Vĩ độ (không bắt buộc)</FormLabel>
              <Input
                type="number"
                step="any"
                value={formData.location?.coordinates?.latitude || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location: {
                      ...formData.location!,
                      coordinates: {
                        ...formData.location!.coordinates!,
                        latitude: parseFloat(e.target.value) || 0,
                      },
                    },
                  })
                }
                placeholder="21.0278"
              />
            </FormField>

            <FormField>
              <FormLabel>Kinh độ (không bắt buộc)</FormLabel>
              <Input
                type="number"
                step="any"
                value={formData.location?.coordinates?.longitude || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location: {
                      ...formData.location!,
                      coordinates: {
                        ...formData.location!.coordinates!,
                        longitude: parseFloat(e.target.value) || 0,
                      },
                    },
                  })
                }
                placeholder="105.8342"
              />
            </FormField>
          </div>

          {errors.submit && <FormError>{errors.submit}</FormError>}

          {/* Cloudflare Turnstile Captcha */}
          {TURNSTILE_SITE_KEY && (
            <FormField>
              <FormLabel required>Xác minh bạn là người thật</FormLabel>
              <Turnstile
                siteKey={TURNSTILE_SITE_KEY}
                onVerify={(token) => setTurnstileToken(token)}
                onExpire={() => setTurnstileToken("")}
                onError={() => setErrors({ captcha: "Xác thực captcha không thành công. Vui lòng thử lại." })}
                theme="auto"
                className="mt-2"
              />
              {errors.captcha && <FormError>{errors.captcha}</FormError>}
            </FormField>
          )}

          <div className="flex gap-4 mt-6">
            <Button type="submit" disabled={createMutation.isPending} className="flex-1">
              {createMutation.isPending ? "Đang gửi..." : "Gửi báo cáo"}
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default PublicIncidentReport
