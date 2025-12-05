import { Select } from "../ui/select"
import { Input } from "../ui/input"
import { Input } from "../ui/input"

interface IncidentFiltersProps {
  status?: string
  severity?: string
  search?: string
  onStatusChange: (status: string) => void
  onSeverityChange: (severity: string) => void
  onSearchChange: (search: string) => void
}

export const IncidentFilters: React.FC<IncidentFiltersProps> = ({
  status,
  severity,
  search,
  onStatusChange,
  onSeverityChange,
  onSearchChange,
}) => {
  return (
    <div className="flex flex-wrap gap-4 mb-4">
      <div className="flex-1 min-w-[200px]">
        <Input
          placeholder="Search incidents..."
          value={search || ""}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <div className="w-[180px]">
        <Select
          value={status || ""}
          onChange={(e) => onStatusChange(e.target.value)}
          placeholder="All Statuses"
        >
          <option value="">All Statuses</option>
          <option value="reported">Reported</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In Progress</option>
          <option value="waiting_approval">Waiting Approval</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </Select>
      </div>
      <div className="w-[180px]">
        <Select
          value={severity || ""}
          onChange={(e) => onSeverityChange(e.target.value)}
          placeholder="All Severities"
        >
          <option value="">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </Select>
      </div>
    </div>
  )
}
