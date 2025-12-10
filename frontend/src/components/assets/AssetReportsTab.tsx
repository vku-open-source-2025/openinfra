import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { assetsApi } from "../../api/assets";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Skeleton } from "../ui/skeleton";
import { Download, FileText, FileSpreadsheet } from "lucide-react";
import { ReportGenerator } from "./ReportGenerator";

interface AssetReportsTabProps {
  assetId: string;
}

const AssetReportsTab: React.FC<AssetReportsTabProps> = ({ assetId }) => {
  const [reportType, setReportType] = useState<
    "maintenance_summary" | "incident_summary" | "lifecycle_overview" | "end_of_life_forecast" | "custom"
  >("maintenance_summary");
  const [format, setFormat] = useState<"pdf" | "excel">("pdf");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [costMin, setCostMin] = useState("");
  const [costMax, setCostMax] = useState("");
  const [generatedReport, setGeneratedReport] = useState<{ report_url: string; report_id: string } | null>(null);

  const generateMutation = useMutation({
    mutationFn: () =>
      assetsApi.generateReport(assetId, reportType, format, {
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        severity: severityFilter || undefined,
        cost_min: costMin ? parseFloat(costMin) : undefined,
        cost_max: costMax ? parseFloat(costMax) : undefined,
      }),
    onSuccess: (data) => {
      setGeneratedReport(data);
    },
  });

  const handleGenerate = () => {
    generateMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Report Generation */}
      <div className="bg-slate-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Tạo báo cáo</h3>
        <ReportGenerator
          reportType={reportType}
          format={format}
          dateFrom={dateFrom}
          dateTo={dateTo}
          severityFilter={severityFilter}
          costMin={costMin}
          costMax={costMax}
          onReportTypeChange={setReportType}
          onFormatChange={setFormat}
          onDateFromChange={setDateFrom}
          onDateToChange={setDateTo}
          onSeverityFilterChange={setSeverityFilter}
          onCostMinChange={setCostMin}
          onCostMaxChange={setCostMax}
          onGenerate={handleGenerate}
          isGenerating={generateMutation.isPending}
        />
      </div>

      {/* Generated Report */}
      {generatedReport && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-green-900 mb-1">Tạo báo cáo thành công</h4>
              <p className="text-sm text-green-700">Mã báo cáo: {generatedReport.report_id}</p>
            </div>
            <Button
              onClick={() => window.open(generatedReport.report_url, "_blank")}
              className="bg-green-600 hover:bg-green-700"
            >
              {format === "pdf" ? (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Tải PDF
                </>
              ) : (
                <>
                  <FileSpreadsheet className="h-4 w-4 mr-2" />
                  Tải Excel
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Report History Placeholder */}
      <div className="bg-slate-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Lịch sử báo cáo đã tạo</h3>
        <div className="text-center py-8 text-slate-500">
          <FileText size={48} className="mx-auto mb-4 opacity-50" />
          <p>Lịch sử báo cáo sẽ hiển thị tại đây</p>
          <p className="text-xs mt-1">(Tính năng đang triển khai)</p>
        </div>
      </div>
    </div>
  );
};

export default AssetReportsTab;
