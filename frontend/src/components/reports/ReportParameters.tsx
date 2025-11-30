import { Form, FormField, FormLabel } from "../ui/form"
import { Input } from "../ui/input"
import { Select } from "../ui/select"
import { DatePicker } from "../ui/date-picker"
import type { ReportType } from "../../types/report"

interface ReportParametersProps {
  reportType: ReportType
  parameters: Record<string, any>
  onParametersChange: (parameters: Record<string, any>) => void
}

export const ReportParameters: React.FC<ReportParametersProps> = ({
  reportType,
  parameters,
  onParametersChange,
}) => {
  const updateParameter = (key: string, value: any) => {
    onParametersChange({ ...parameters, [key]: value })
  }

  if (reportType === "maintenance") {
    return (
      <Form>
        <FormField>
          <FormLabel>Status</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </Select>
        </FormField>
        <FormField>
          <FormLabel>From Date</FormLabel>
          <DatePicker
            value={parameters.from_date ? new Date(parameters.from_date) : null}
            onChange={(date) => updateParameter("from_date", date?.toISOString())}
          />
        </FormField>
        <FormField>
          <FormLabel>To Date</FormLabel>
          <DatePicker
            value={parameters.to_date ? new Date(parameters.to_date) : null}
            onChange={(date) => updateParameter("to_date", date?.toISOString())}
          />
        </FormField>
      </Form>
    )
  }

  if (reportType === "budget") {
    return (
      <Form>
        <FormField>
          <FormLabel>Fiscal Year</FormLabel>
          <Input
            type="number"
            value={parameters.fiscal_year || ""}
            onChange={(e) => updateParameter("fiscal_year", parseInt(e.target.value) || null)}
            placeholder={new Date().getFullYear().toString()}
          />
        </FormField>
        <FormField>
          <FormLabel>Status</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Submitted</option>
            <option value="approved">Approved</option>
          </Select>
        </FormField>
      </Form>
    )
  }

  if (reportType === "incident") {
    return (
      <Form>
        <FormField>
          <FormLabel>Severity</FormLabel>
          <Select
            value={parameters.severity || ""}
            onChange={(e) => updateParameter("severity", e.target.value)}
          >
            <option value="">All Severities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </Select>
        </FormField>
        <FormField>
          <FormLabel>Status</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="reported">Reported</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </Select>
        </FormField>
        <FormField>
          <FormLabel>From Date</FormLabel>
          <DatePicker
            value={parameters.from_date ? new Date(parameters.from_date) : null}
            onChange={(date) => updateParameter("from_date", date?.toISOString())}
          />
        </FormField>
        <FormField>
          <FormLabel>To Date</FormLabel>
          <DatePicker
            value={parameters.to_date ? new Date(parameters.to_date) : null}
            onChange={(date) => updateParameter("to_date", date?.toISOString())}
          />
        </FormField>
      </Form>
    )
  }

  if (reportType === "asset") {
    return (
      <Form>
        <FormField>
          <FormLabel>Feature Type</FormLabel>
          <Input
            value={parameters.feature_type || ""}
            onChange={(e) => updateParameter("feature_type", e.target.value)}
            placeholder="e.g., road, bridge, building"
          />
        </FormField>
        <FormField>
          <FormLabel>Status</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="maintenance">Maintenance</option>
          </Select>
        </FormField>
      </Form>
    )
  }

  return null
}
