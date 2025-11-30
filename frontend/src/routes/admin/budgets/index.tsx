import { createFileRoute } from '@tanstack/react-router';
import BudgetList from '@/pages/budgets/BudgetList';

export const Route = createFileRoute('/admin/budgets/')({
  component: BudgetList,
});
