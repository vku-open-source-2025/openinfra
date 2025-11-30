import { createFileRoute } from '@tanstack/react-router';
import IncidentCreate from '@/pages/incidents/IncidentCreate';

export const Route = createFileRoute('/admin/incidents/create')({
  component: IncidentCreate,
});
