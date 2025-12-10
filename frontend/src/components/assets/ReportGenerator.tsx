import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Select } from "../ui/select";

interface ReportGeneratorProps {
  reportType: "maintenance_summary" | "incident_summary" | "lifecycle_overview" | "end_of_life_forecast" | "custom";
  format: "pdf" | "excel";
  dateFrom: string;
  dateTo: string;
  severityFilter: string;
  costMin: string;
  costMax: string;
  onReportTypeChange: (type: typeof reportType) => void;
  onFormatChange: (format: typeof format) => void;
  onDateFromChange: (date: string) => void;
  onDateToChange: (date: string) => void;
  onSeverityFilterChange: (severity: string) => void;
  onCostMinChange: (cost: string) => void;
  onCostMaxChange: (cost: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export const ReportGenerator: React.FC<ReportGeneratorProps> = ({
  reportType,
  format,
  dateFrom,
  dateTo,
  severityFilter,
  costMin,
  costMax,
  onReportTypeChange,
  onFormatChange,
  onDateFromChange,
  onDateToChange,
  onSeverityFilterChange,
  onCostMinChange,
  onCostMaxChange,
  onGenerate,
  isGenerating,
}) => {
  return (
    <div className="space-y-4">
      {/* Report Type Selection */}
      <div>
        <label className="text-xs text-slate-500 uppercase tracking-wide mb-2 block">Chọn loại báo cáo</label>
        <div className="space-y-2">
          <label className="flex items-center gap-2 p-3 border border-slate-200 rounded cursor-pointer hover:bg-slate-50">
            <input
              type="radio"
              name="reportType"
              value="maintenance_summary"
              checked={reportType === "maintenance_summary"}
              onChange={() => onReportTypeChange("maintenance_summary")}
              className="rounded border-slate-300"
            />
            <span className="text-sm text-slate-900">Tóm tắt bảo trì</span>
          </label>
          <label className="flex items-center gap-2 p-3 border border-slate-200 rounded cursor-pointer hover:bg-slate-50">
            <input
              type="radio"
              name="reportType"
              value="incident_summary"
              checked={reportType === "incident_summary"}
              onChange={() => onReportTypeChange("incident_summary")}
              className="rounded border-slate-300"
            />
            <span className="text-sm text-slate-900">Tóm tắt sự cố</span>
          </label>
          <label className="flex items-center gap-2 p-3 border border-slate-200 rounded cursor-pointer hover:bg-slate-50">
            <input
              type="radio"
              name="reportType"
              value="lifecycle_overview"
              checked={reportType === "lifecycle_overview"}
              onChange={() => onReportTypeChange("lifecycle_overview")}
              className="rounded border-slate-300"
            />
            <span className="text-sm text-slate-900">Tổng quan vòng đời</span>
          </label>
          <label className="flex items-center gap-2 p-3 border border-slate-200 rounded cursor-pointer hover:bg-slate-50">
            <input
              type="radio"
              name="reportType"
              value="end_of_life_forecast"
              checked={reportType === "end_of_life_forecast"}
              onChange={() => onReportTypeChange("end_of_life_forecast")}
              className="rounded border-slate-300"
            />
            <span className="text-sm text-slate-900">Dự báo hết vòng đời</span>
          </label>
          <label className="flex items-center gap-2 p-3 border border-slate-200 rounded cursor-pointer hover:bg-slate-50">
            <input
              type="radio"
              name="reportType"
              value="custom"
              checked={reportType === "custom"}
              onChange={() => onReportTypeChange("custom")}
              className="rounded border-slate-300"
            />
            <span className="text-sm text-slate-900">Báo cáo tùy chỉnh</span>
          </label>
        </div>
      </div>

      {/* Filters (if custom) */}
      {reportType === "custom" && (
        <div className="space-y-4 border-t border-slate-200 pt-4">
          <h4 className="text-sm font-semibold text-slate-900">Bộ lọc</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Từ ngày</label>
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => onDateFromChange(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Đến ngày</label>
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => onDateToChange(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Mức độ sự cố</label>
              <Select
                value={severityFilter}
                onValueChange={onSeverityFilterChange}
              >
                <option value="">Tất cả mức độ</option>
                <option value="low">Thấp</option>
                <option value="medium">Trung bình</option>
                <option value="high">Cao</option>
                <option value="critical">Nghiêm trọng</option>
              </Select>
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Khoảng chi phí bảo trì</label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={costMin}
                  onChange={(e) => onCostMinChange(e.target.value)}
                  placeholder="Tối thiểu"
                />
                <Input
                  type="number"
                  value={costMax}
                  onChange={(e) => onCostMaxChange(e.target.value)}
                  placeholder="Tối đa"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Output Format */}
      <div className="border-t border-slate-200 pt-4">
        <label className="text-xs text-slate-500 uppercase tracking-wide mb-2 block">Định dạng đầu ra</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="format"
              value="pdf"
              checked={format === "pdf"}
              onChange={() => onFormatChange("pdf")}
              className="rounded border-slate-300"
            />
            <span className="text-sm text-slate-900">PDF</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="format"
              value="excel"
              checked={format === "excel"}
              onChange={() => onFormatChange("excel")}
              className="rounded border-slate-300"
            />
            <span className="text-sm text-slate-900">Excel</span>
          </label>
        </div>
      </div>

      {/* Generate Button */}
      <div className="border-t border-slate-200 pt-4">
        <Button
          onClick={onGenerate}
          disabled={isGenerating}
          className="w-full"
        >
          {isGenerating ? "Đang tạo báo cáo..." : "Tạo báo cáo"}
        </Button>
      </div>
    </div>
  );
};
