import { createFileRoute, Outlet, useRouterState } from '@tanstack/react-router';

import EmergencyCenter from '@/pages/emergency/EmergencyCenter';

const BASE_EMERGENCY_CENTER_PATH = '/admin/emergency-center';

function EmergencyCenterRouteLayout() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const normalizedPathname = pathname.endsWith('/') && pathname !== '/' ? pathname.slice(0, -1) : pathname;

  if (normalizedPathname === BASE_EMERGENCY_CENTER_PATH) {
    return <EmergencyCenter />;
  }

  return <Outlet />;
}

export const Route = createFileRoute('/admin/emergency-center')({
  component: EmergencyCenterRouteLayout,
});
