import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { publicApi } from "../../api/public"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Textarea } from "../../components/ui/textarea"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import type { IncidentCreateRequest, IncidentSeverity } from "../../types/incident"

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

  const createMutation = useMutation({
    mutationFn: (data: IncidentCreateRequest) => publicApi.createAnonymousIncident(data),
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

    createMutation.mutate(formData as IncidentCreateRequest)
  }

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Report an Incident</h1>
        <p className="text-slate-600 mb-8">
          Help us improve our infrastructure by reporting issues you encounter.
        </p>

        <Form onSubmit={handleSubmit}>
          <FormField>
            <FormLabel required>What happened?</FormLabel>
            <Input
              value={formData.title || ""}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Brief description (e.g., Pothole on Main Street)"
            />
            {errors.title && <FormError>{errors.title}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Details</FormLabel>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Provide more details about the incident..."
              rows={5}
            />
            {errors.description && <FormError>{errors.description}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Severity</FormLabel>
            <Select
              value={formData.severity || "medium"}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value as IncidentSeverity })}
            >
              <option value="low">Low - Minor issue</option>
              <option value="medium">Medium - Moderate issue</option>
              <option value="high">High - Significant issue</option>
              <option value="critical">Critical - Urgent attention needed</option>
            </Select>
          </FormField>

          <FormField>
            <FormLabel required>Location</FormLabel>
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
              placeholder="Street address or location description"
            />
            {errors.address && <FormError>{errors.address}</FormError>}
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField>
              <FormLabel>Latitude (optional)</FormLabel>
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
              <FormLabel>Longitude (optional)</FormLabel>
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

          <div className="flex gap-4 mt-6">
            <Button type="submit" disabled={createMutation.isPending} className="flex-1">
              {createMutation.isPending ? "Submitting..." : "Submit Report"}
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default PublicIncidentReport
