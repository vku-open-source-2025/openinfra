import { createFileRoute } from '@tanstack/react-router';
import SensorList from '@/pages/iot/SensorList';

export const Route = createFileRoute('/admin/iot/')({
  component: SensorList,
});
