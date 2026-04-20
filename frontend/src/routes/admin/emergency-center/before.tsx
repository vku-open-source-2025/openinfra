import { createFileRoute } from '@tanstack/react-router';

import BeforeDisasterBoardPage from '@/pages/emergency/phases/BeforeDisasterBoardPage';

export const Route = createFileRoute('/admin/emergency-center/before')({
  component: BeforeDisasterBoardPage,
});
