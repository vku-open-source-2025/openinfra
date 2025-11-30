import { createFileRoute } from '@tanstack/react-router';
import ReportCreate from '@/pages/reports/ReportCreate';

export const Route = createFileRoute('/admin/reports/create')({
  component: ReportCreate,
});
