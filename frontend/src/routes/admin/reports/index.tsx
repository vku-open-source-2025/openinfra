import { createFileRoute } from '@tanstack/react-router';
import ReportList from '@/pages/reports/ReportList';

export const Route = createFileRoute('/admin/reports/')({
  component: ReportList,
});
