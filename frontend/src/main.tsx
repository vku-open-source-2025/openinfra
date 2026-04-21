import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import 'leaflet/dist/leaflet.css';
import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createRouter } from '@tanstack/react-router';
import { queryClient } from './lib/queryClient';

// Import the generated route tree
import { routeTree } from './routeTree.gen';

function getRootElement() {
  const existingRoot = document.getElementById('root');
  if (existingRoot) {
    return existingRoot;
  }

  const root = document.createElement('div');
  root.id = 'root';
  document.body.appendChild(root);
  return root;
}

// Create a new router instance
const router = createRouter({
  routeTree,
  context: {
    queryClient,
  },
  defaultPreload: 'intent',
  defaultPreloadStaleTime: 0,
});

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

ReactDOM.createRoot(getRootElement()).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)
