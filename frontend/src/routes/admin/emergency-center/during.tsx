import { createFileRoute } from '@tanstack/react-router';

import DuringDisasterBoardPage from '@/pages/emergency/phases/DuringDisasterBoardPage';

export const Route = createFileRoute('/admin/emergency-center/during')({
  component: DuringDisasterBoardPage,
});
