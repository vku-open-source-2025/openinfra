import { createFileRoute } from '@tanstack/react-router';
import IncidentList from '@/pages/incidents/IncidentList';

export const Route = createFileRoute('/admin/incidents/')({
  component: IncidentList,
});
