import { createRootRoute, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';
import AIChatWidget from '../components/AIChatWidget';

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet />
      <AIChatWidget />
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  ),
});
