import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { reportsApi } from "../../api/reports"
import { ReportParameters } from "../../components/reports/ReportParameters"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import { ArrowLeft } from "lucide-react"
import type { ReportType, ReportFormat, ReportCreateRequest } from "../../types/report"

const ReportCreate: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<Partial<ReportCreateRequest>>({
    type: "maintenance",
    format: "pdf",
    parameters: {},
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const createMutation = useMutation({
    mutationFn: (data: ReportCreateRequest) => reportsApi.create(data),
    onSuccess: (report) => {
      queryClient.invalidateQueries({ queryKey: ["reports"] })
      navigate({ to: "/admin/reports" })
    },
    onError: (error: any) => {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData as ReportCreateRequest)
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/reports" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Reports
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Generate Report</h1>

        <Form onSubmit={handleSubmit}>
          <FormField>
            <FormLabel required>Report Type</FormLabel>
            <Select
              value={formData.type || "maintenance"}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  type: e.target.value as ReportType,
                  parameters: {}, // Reset parameters when type changes
                })
              }}
            >
              <option value="maintenance">Maintenance</option>
              <option value="budget">Budget</option>
              <option value="incident">Incident</option>
              <option value="asset">Asset</option>
            </Select>
          </FormField>

          <FormField>
            <FormLabel required>Format</FormLabel>
            <Select
              value={formData.format || "pdf"}
              onChange={(e) =>
                setFormData({ ...formData, format: e.target.value as ReportFormat })
              }
            >
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
              <option value="csv">CSV</option>
            </Select>
          </FormField>

          <div className="mt-6 pt-6 border-t">
            <h3 className="font-semibold mb-4">Report Parameters</h3>
            <ReportParameters
              reportType={formData.type as ReportType}
              parameters={formData.parameters || {}}
              onParametersChange={(parameters) =>
                setFormData({ ...formData, parameters })
              }
            />
          </div>

          {errors.submit && <FormError>{errors.submit}</FormError>}

          <div className="flex gap-4 mt-6">
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Generating..." : "Generate Report"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate({ to: "/admin/reports" })}
            >
              Cancel
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default ReportCreate
