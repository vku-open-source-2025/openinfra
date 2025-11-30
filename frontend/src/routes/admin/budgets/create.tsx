import { createFileRoute } from '@tanstack/react-router';
import BudgetCreate from '@/pages/budgets/BudgetCreate';

export const Route = createFileRoute('/admin/budgets/create')({
  component: BudgetCreate,
});
