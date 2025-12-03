import { createFileRoute } from '@tanstack/react-router';
import DataIngest from '../../pages/admin/DataIngest';

export const Route = createFileRoute('/admin/ingest')({
  component: DataIngest,
});
