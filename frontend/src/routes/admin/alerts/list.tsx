import { createFileRoute } from '@tanstack/react-router';
import AlertList from '@/pages/alerts/AlertList';

export const Route = createFileRoute('/admin/alerts/list')({
  component: AlertList,
});
