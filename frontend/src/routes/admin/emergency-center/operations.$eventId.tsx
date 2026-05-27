import { createFileRoute } from '@tanstack/react-router';

import RescueOperationPage from '@/pages/emergency/RescueOperationPage';

export const Route = createFileRoute('/admin/emergency-center/operations/$eventId')({
  component: RescueOperationPage,
});
