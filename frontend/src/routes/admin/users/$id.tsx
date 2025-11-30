import { createFileRoute } from '@tanstack/react-router';
import UserDetail from '@/pages/admin/UserDetail';

export const Route = createFileRoute('/admin/users/$id')({
  component: UserDetail,
});
