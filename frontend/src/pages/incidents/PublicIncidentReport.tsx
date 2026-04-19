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
import type { IncidentCategory, IncidentCreateRequest, IncidentSeverity } from "../../types/incident"

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || ""

const PublicIncidentReport: React.FC = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState<Partial<IncidentCreateRequest>>({
    title: "",
    description: "",
    category: "other",
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
  const [lookupReference, setLookupReference] = useState("")
  const [lookupError, setLookupError] = useState("")
  const [turnstileToken, setTurnstileToken] = useState<string>("")

  const createMutation = useMutation({
    mutationFn: (data: IncidentCreateRequest) => publicApi.createAnonymousIncident(data, turnstileToken),
    onSuccess: (incident) => {
      navigate({
        to: "/public/incidents/$incidentId",
        params: { incidentId: incident.incident_number || incident.id },
      })
    },
    onError: (error: any) => {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      }
    },
  })

  const lookupMutation = useMutation({
    mutationFn: (reference: string) => publicApi.lookupPublicIncident(reference),
    onSuccess: (incident) => {
      setLookupError("")
      navigate({
        to: "/public/incidents/$incidentId",
        params: { incidentId: incident.incident_number || incident.id },
      })
    },
    onError: () => {
      setLookupError("Không tìm thấy báo cáo. Vui lòng kiểm tra lại mã báo cáo hoặc ID.")
    },
  })

  const handleLookupSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const reference = lookupReference.trim()
    if (!reference) {
      setLookupError("Vui lòng nhập mã báo cáo hoặc ID")
      return
    }

    setLookupError("")
    lookupMutation.mutate(reference)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!formData.title?.trim()) {
      setErrors({ title: "Tiêu đề là bắt buộc" })
      return
    }
    if (!formData.description?.trim()) {
      setErrors({ description: "Mô tả là bắt buộc" })
      return
    }
    if (!formData.category) {
      setErrors({ category: "Loại sự cố là bắt buộc" })
      return
    }
    if (!formData.location?.address?.trim()) {
      setErrors({ address: "Địa chỉ là bắt buộc" })
      return
    }
    if (TURNSTILE_SITE_KEY && !turnstileToken) {
      setErrors({ captcha: "Vui lòng hoàn thành xác thực captcha" })
      return
    }

    const submitData: IncidentCreateRequest = {
      title: formData.title.trim(),
      description: formData.description.trim(),
      category: formData.category,
      severity: formData.severity || "medium",
      location: {
        address: formData.location?.address?.trim(),
        geometry: {
          type: "Point",
          coordinates: [
            formData.location?.coordinates?.longitude || 0,
            formData.location?.coordinates?.latitude || 0,
          ],
        },
      },
    }

    createMutation.mutate(submitData)
  }

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Báo sự cố</h1>
        <p className="text-slate-600 mb-8">
          Hãy giúp chúng tôi cải thiện hạ tầng bằng cách báo các vấn đề bạn gặp phải.
        </p>

        <div id="lookup-status" className="mb-8 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h2 className="text-base font-semibold text-slate-900 mb-1">Tra cứu trạng thái báo cáo</h2>
          <p className="text-sm text-slate-600 mb-3">Nhập mã báo cáo (ví dụ: INC-2026-ABC123) hoặc ID báo cáo.</p>
          <form onSubmit={handleLookupSubmit} className="flex flex-col sm:flex-row gap-3">
            <Input
              value={lookupReference}
              onChange={(e) => setLookupReference(e.target.value)}
              placeholder="INC-2026-ABC123 hoặc 67f..."
            />
            <Button type="submit" variant="outline" disabled={lookupMutation.isPending}>
              {lookupMutation.isPending ? "Đang tra cứu..." : "Tra cứu"}
            </Button>
          </form>
          {lookupError && <p className="mt-2 text-sm text-red-600">{lookupError}</p>}
        </div>

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
            <FormLabel required>Loại sự cố</FormLabel>
            <Select
              value={formData.category || "other"}
              onChange={(e) => setFormData({ ...formData, category: e.target.value as IncidentCategory })}
            >
              <option value="malfunction">Không hoạt động / Hỏng</option>
              <option value="damage">Hư hỏng vật lý</option>
              <option value="safety_hazard">Nguy hiểm an toàn</option>
              <option value="vandalism">Phá hoại</option>
              <option value="other">Khác</option>
            </Select>
            {errors.category && <FormError>{errors.category}</FormError>}
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
