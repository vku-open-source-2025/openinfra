import { createFileRoute } from '@tanstack/react-router';
import PublicIncidentReport from '@/pages/incidents/PublicIncidentReport';

export const Route = createFileRoute('/public/report')({
  component: PublicIncidentReport,
});
