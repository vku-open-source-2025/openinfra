import { createFileRoute } from '@tanstack/react-router';
import IncidentDetail from '@/pages/incidents/IncidentDetail';

export const Route = createFileRoute('/admin/incidents/$id')({
  component: IncidentDetail,
});
