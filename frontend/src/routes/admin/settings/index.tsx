import { createFileRoute } from '@tanstack/react-router';
import ProfileSettings from '@/pages/settings/ProfileSettings';

export const Route = createFileRoute('/admin/settings/')({
  component: ProfileSettings,
});
