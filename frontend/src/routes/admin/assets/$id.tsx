import { createFileRoute } from '@tanstack/react-router';
import AssetDetail from '@/pages/admin/AssetDetail';

export const Route = createFileRoute('/admin/assets/$id')({
  component: AssetDetail,
});
