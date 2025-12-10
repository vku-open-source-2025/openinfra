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
          <FormLabel>Trạng thái</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">Tất cả trạng thái</option>
            <option value="scheduled">Đã lên lịch</option>
            <option value="in_progress">Đang thực hiện</option>
            <option value="completed">Hoàn thành</option>
            <option value="cancelled">Bị hủy</option>
          </Select>
        </FormField>
        <FormField>
          <FormLabel>Từ ngày</FormLabel>
          <DatePicker
            value={parameters.from_date ? new Date(parameters.from_date) : null}
            onChange={(date) => updateParameter("from_date", date?.toISOString())}
          />
        </FormField>
        <FormField>
          <FormLabel>Đến ngày</FormLabel>
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
          <FormLabel>Năm tài chính</FormLabel>
          <Input
            type="number"
            value={parameters.fiscal_year || ""}
            onChange={(e) => updateParameter("fiscal_year", parseInt(e.target.value) || null)}
            placeholder={new Date().getFullYear().toString()}
          />
        </FormField>
        <FormField>
          <FormLabel>Trạng thái</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">Tất cả trạng thái</option>
            <option value="draft">Bản nháp</option>
            <option value="submitted">Đã gửi</option>
            <option value="approved">Đã phê duyệt</option>
          </Select>
        </FormField>
      </Form>
    )
  }

  if (reportType === "incident") {
    return (
      <Form>
        <FormField>
          <FormLabel>Mức nghiêm trọng</FormLabel>
          <Select
            value={parameters.severity || ""}
            onChange={(e) => updateParameter("severity", e.target.value)}
          >
            <option value="">Tất cả mức độ</option>
            <option value="low">Thấp</option>
            <option value="medium">Trung bình</option>
            <option value="high">Cao</option>
            <option value="critical">Nguy kịch</option>
          </Select>
        </FormField>
        <FormField>
          <FormLabel>Trạng thái</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">Tất cả trạng thái</option>
            <option value="reported">Đã báo cáo</option>
            <option value="resolved">Đã xử lý</option>
            <option value="closed">Đã đóng</option>
          </Select>
        </FormField>
        <FormField>
          <FormLabel>Từ ngày</FormLabel>
          <DatePicker
            value={parameters.from_date ? new Date(parameters.from_date) : null}
            onChange={(date) => updateParameter("from_date", date?.toISOString())}
          />
        </FormField>
        <FormField>
          <FormLabel>Đến ngày</FormLabel>
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
          <FormLabel>Loại tài sản</FormLabel>
          <Input
            value={parameters.feature_type || ""}
            onChange={(e) => updateParameter("feature_type", e.target.value)}
            placeholder="ví dụ: đường, cầu, tòa nhà"
          />
        </FormField>
        <FormField>
          <FormLabel>Trạng thái</FormLabel>
          <Select
            value={parameters.status || ""}
            onChange={(e) => updateParameter("status", e.target.value)}
          >
            <option value="">Tất cả trạng thái</option>
            <option value="active">Hoạt động</option>
            <option value="inactive">Ngưng hoạt động</option>
            <option value="maintenance">Bảo trì</option>
          </Select>
        </FormField>
      </Form>
    )
  }

  return null
}
