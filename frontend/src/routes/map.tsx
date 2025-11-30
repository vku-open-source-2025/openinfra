import { createFileRoute } from '@tanstack/react-router';
import PublicMap from '../pages/PublicMap';

export const Route = createFileRoute('/map')({
  component: PublicMap,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      assetId: search.assetId as string | undefined,
    };
  },
});
