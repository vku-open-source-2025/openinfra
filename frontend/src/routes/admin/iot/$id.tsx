import { createFileRoute } from '@tanstack/react-router';
import SensorDetail from '@/pages/iot/SensorDetail';

export const Route = createFileRoute('/admin/iot/$id')({
  component: SensorDetail,
});
