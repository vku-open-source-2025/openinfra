import { createFileRoute } from '@tanstack/react-router';
import SensorCreate from '@/pages/iot/SensorCreate';

export const Route = createFileRoute('/admin/iot/create')({
  component: SensorCreate,
});
