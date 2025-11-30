import { createFileRoute } from '@tanstack/react-router';
import BudgetDetail from '@/pages/budgets/BudgetDetail';

export const Route = createFileRoute('/admin/budgets/$id')({
  component: BudgetDetail,
});
