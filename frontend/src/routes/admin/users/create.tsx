import { createFileRoute } from '@tanstack/react-router';
import UserCreate from '@/pages/admin/UserCreate';

export const Route = createFileRoute('/admin/users/create')({
  component: UserCreate,
});
