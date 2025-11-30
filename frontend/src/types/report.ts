export type ReportType = 'maintenance' | 'budget' | 'incident' | 'asset';
export type ReportFormat = 'pdf' | 'excel' | 'csv';
export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed';

export interface Report {
  id: string;
  report_code: string;
  type: ReportType;
  format: ReportFormat;
  status: ReportStatus;
  parameters: Record<string, any>;
  file_url?: string;
  created_at: string;
  completed_at?: string;
}

export interface ReportCreateRequest {
  type: ReportType;
  format: ReportFormat;
  parameters: Record<string, any>;
}
