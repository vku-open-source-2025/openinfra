import { Select } from "../ui/select"
import { Input } from "../ui/input"

interface IncidentFiltersProps {
  status?: string
  severity?: string
  search?: string
  day?: string
  onStatusChange: (status: string) => void
  onSeverityChange: (severity: string) => void
  onSearchChange: (search: string) => void
  onDayChange: (day: string) => void
}

export const IncidentFilters: React.FC<IncidentFiltersProps> = ({
  status,
  severity,
  search,
  day,
  onStatusChange,
  onSeverityChange,
  onSearchChange,
  onDayChange,
}) => {
  return (
    <div className="flex flex-wrap gap-4 mb-4">
      <div className="flex-1 min-w-[200px]">
        <Input
          placeholder="Tìm kiếm sự cố..."
          value={search || ""}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <div className="w-[180px]">
        <Select
          value={status || ""}
          onChange={(e) => onStatusChange(e.target.value)}
          placeholder="Tất cả trạng thái"
        >
          <option value="">Tất cả trạng thái</option>
          <option value="reported">Đã báo cáo</option>
          <option value="acknowledged">Đã nhận</option>
          <option value="assigned">Đã phân công</option>
          <option value="in_progress">Đang thực hiện</option>
          <option value="waiting_approval">Đang chờ phê duyệt</option>
          <option value="resolved">Đã xử lý</option>
          <option value="closed">Đã đóng</option>
        </Select>
      </div>
      <div className="w-[180px]">
        <Select
          value={severity || ""}
          onChange={(e) => onSeverityChange(e.target.value)}
          placeholder="Tất cả mức độ"
        >
          <option value="">Tất cả mức độ</option>
          <option value="low">Thấp</option>
          <option value="medium">Trung bình</option>
          <option value="high">Cao</option>
          <option value="critical">Nghiêm trọng</option>
        </Select>
      </div>
      <div className="w-[200px]">
        <Input
          type="date"
          value={day || ""}
          onChange={(e) => onDayChange(e.target.value)}
        />
      </div>
    </div>
  )
}
