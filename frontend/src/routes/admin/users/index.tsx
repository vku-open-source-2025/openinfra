import { createFileRoute } from '@tanstack/react-router';
import UserList from '@/pages/admin/UserList';

export const Route = createFileRoute('/admin/users/')({
  component: UserList,
});
