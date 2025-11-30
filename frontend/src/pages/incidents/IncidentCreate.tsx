import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { incidentsApi } from "../../api/incidents"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Textarea } from "../../components/ui/textarea"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import { ArrowLeft } from "lucide-react"
import type { IncidentCreateRequest, IncidentSeverity } from "../../types/incident"

const IncidentCreate: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
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
    mutationFn: (data: IncidentCreateRequest) => incidentsApi.create(data),
    onSuccess: (incident) => {
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
      navigate({ to: `/admin/incidents/${incident.id}` })
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
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/incidents" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Incidents
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Report New Incident</h1>

        <Form onSubmit={handleSubmit}>
          <FormField>
            <FormLabel required>Title</FormLabel>
            <Input
              value={formData.title || ""}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Brief description of the incident"
            />
            {errors.title && <FormError>{errors.title}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Description</FormLabel>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Detailed description of the incident"
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
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </Select>
          </FormField>

          <FormField>
            <FormLabel required>Location Address</FormLabel>
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
              placeholder="Street address or location"
            />
            {errors.address && <FormError>{errors.address}</FormError>}
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField>
              <FormLabel>Latitude</FormLabel>
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
              <FormLabel>Longitude</FormLabel>
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
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Incident"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate({ to: "/admin/incidents" })}
            >
              Cancel
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default IncidentCreate
