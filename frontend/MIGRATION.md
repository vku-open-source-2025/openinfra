# Tech Stack Migration Guide

## Overview

This document outlines the successful migration from React Router DOM to TanStack Router, along with the integration of modern React state management and HTTP client solutions.

## What Changed

### 1. Routing System - React Router DOM → TanStack Router

**Before:**
```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

<BrowserRouter>
  <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/map" element={<PublicMap />} />
    <Route path="/admin" element={<Dashboard />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
</BrowserRouter>
```

**After:**
```tsx
import { RouterProvider, createRouter } from '@tanstack/react-router';
import { routeTree } from './routeTree.gen';

const router = createRouter({
  routeTree,
  context: { queryClient },
  defaultPreload: 'intent',
});

<RouterProvider router={router} />
```

**Migration Steps:**
- Created file-based routing structure in `src/routes/`
- Routes are now defined in separate files (e.g., `src/routes/index.tsx`, `src/routes/map.tsx`)
- TanStack Router auto-generates route tree at build time
- Better TypeScript support with automatic route type inference

### 2. Navigation - Link and useNavigate

**Before:**
```tsx
import { Link, useNavigate } from 'react-router-dom';

<Link to="/map">Go to Map</Link>

const navigate = useNavigate();
navigate('/admin');
```

**After:**
```tsx
import { Link, useNavigate } from '@tanstack/react-router';

<Link to="/map">Go to Map</Link>

const navigate = useNavigate();
navigate({ to: '/admin' });
```

### 3. Search Params

**Before:**
```tsx
import { useSearchParams } from 'react-router-dom';

const [searchParams, setSearchParams] = useSearchParams();
const assetId = searchParams.get('assetId');
setSearchParams({ assetId: asset._id });
```

**After:**
```tsx
import { useNavigate, useSearch } from '@tanstack/react-router';

const searchParams = useSearch({ from: '/map' });
const assetId = searchParams?.assetId;

const navigate = useNavigate();
navigate({ to: '/map', search: { assetId: asset._id } });
```

### 4. State Management - Zustand

**New Addition:**
```tsx
// src/stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (token, user) => set({ token, user, isAuthenticated: true }),
      logout: () => set({ token: null, user: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' }
  )
);
```

**Usage:**
```tsx
import { useAuthStore } from '@/stores';

function Component() {
  const { user, login, logout } = useAuthStore();
  // ...
}
```

### 5. HTTP Client - Enhanced Axios Configuration

**Before:**
```tsx
// src/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_BASE_API_URL || '/api',
});
```

**After:**
```tsx
// src/lib/httpClient.ts
import axios from 'axios';
import { useAuthStore } from '../stores';

export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_BASE_API_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor for auth tokens
httpClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);
```

### 6. TanStack Query - Enhanced Configuration

**Before:**
```tsx
const queryClient = new QueryClient();
```

**After:**
```tsx
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,        // 5 minutes
      gcTime: 10 * 60 * 1000,          // 10 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: true,
      refetchOnMount: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

### 7. Utility Functions - clsx and tailwind-merge

**New Addition:**
```tsx
// src/lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Usage:**
```tsx
import { cn } from '@/lib/utils';

<div className={cn(
  "base-class",
  isActive && "active-class",
  "hover:bg-blue-500"
)} />
```

## New Project Structure

```
src/
├── components/
│   ├── ui/              # shadcn/ui components (to be added)
│   └── ...              # existing components
├── lib/
│   ├── httpClient.ts    # Axios configuration with interceptors
│   ├── queryClient.ts   # TanStack Query configuration
│   ├── utils.ts         # Utility functions (cn helper)
│   └── index.ts         # Barrel exports
├── routes/
│   ├── __root.tsx       # Root route layout
│   ├── index.tsx        # Home page route
│   ├── map.tsx          # Map page route
│   └── admin.tsx        # Admin dashboard route
├── stores/
│   ├── authStore.ts     # Authentication state
│   ├── appStore.ts      # Application state
│   └── index.ts         # Barrel exports
├── pages/               # Page components
├── hooks/               # Custom hooks
├── api.ts               # API functions (updated to use httpClient)
├── main.tsx             # App entry (updated for TanStack Router)
└── routeTree.gen.ts     # Auto-generated route tree (do not edit)
```

## Configuration Files

### vite.config.ts
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    TanStackRouterVite(),  // Must be before react()
    react()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // ... other config
})
```

### tsconfig.app.json
```json
{
  "compilerOptions": {
    // ... other options
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### components.json (shadcn/ui)
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  }
}
```

## Dependencies Added

```json
{
  "dependencies": {
    "@tanstack/react-router": "^1.139.10",
    "zustand": "^5.0.8",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.4.0",
    "class-variance-authority": "^0.7.1"
  },
  "devDependencies": {
    "@tanstack/router-plugin": "^1.139.10",
    "@tanstack/router-devtools": "^1.139.10"
  }
}
```

## Dependencies Removed

```json
{
  "dependencies": {
    "react-router-dom": "removed"
  }
}
```

## Features & Benefits

### TanStack Router
- **Type-safe routing**: Full TypeScript inference for routes and params
- **File-based routing**: Intuitive route structure matching URL paths
- **Better performance**: Built-in code splitting and route preloading
- **Developer experience**: Auto-generated route tree, devtools support
- **Search params validation**: Type-safe search parameter handling

### Zustand
- **Minimal boilerplate**: Simple and intuitive API
- **Persistence**: Built-in middleware for localStorage persistence
- **TypeScript support**: Excellent type inference
- **DevTools**: Integration with Redux DevTools
- **No context needed**: Direct store access without providers

### Enhanced HTTP Client
- **Authentication**: Automatic token injection via interceptors
- **Error handling**: Centralized error handling and retry logic
- **Request/Response transformation**: Unified request/response handling
- **Timeout management**: Configurable request timeouts
- **401 handling**: Automatic logout and redirect on unauthorized access

### TanStack Query (Enhanced)
- **Smart caching**: Configurable stale time and garbage collection
- **Retry logic**: Exponential backoff for failed requests
- **Window focus refetch**: Auto-refresh data when window gains focus
- **Optimistic updates**: Better UX with optimistic UI updates
- **Mutation error handling**: Centralized mutation error handling

### shadcn/ui Ready
- **Component system**: Ready to add shadcn/ui components
- **Utility function**: `cn()` helper for className merging
- **Configuration**: Components.json already configured
- **Path aliases**: `@/` aliases set up for clean imports

## How to Add shadcn/ui Components

```bash
# Install a component (example: button)
npx shadcn@latest add button

# The component will be added to src/components/ui/button.tsx
```

## Migration Checklist

- [x] Install TanStack Router and dependencies
- [x] Set up Vite plugin for route generation
- [x] Create route files for all existing routes
- [x] Update all Link components to use TanStack Router
- [x] Update all useNavigate hooks
- [x] Update search param handling
- [x] Install and configure Zustand
- [x] Create auth store
- [x] Create app store
- [x] Create enhanced HTTP client with interceptors
- [x] Update API functions to use new HTTP client
- [x] Configure TanStack Query with better defaults
- [x] Install clsx and tailwind-merge
- [x] Create cn utility function
- [x] Set up shadcn/ui configuration
- [x] Update main.tsx with router provider
- [x] Remove react-router-dom dependency
- [x] Delete old App.tsx
- [x] Test application

## Running the Application

```bash
# Install dependencies
pnpm install

# Start dev server
pnpm run dev

# Build for production
pnpm run build
```

## Troubleshooting

### Route tree not generating
- Ensure `@tanstack/router-plugin` is listed BEFORE `react()` in vite.config.ts
- Check that route files are in `src/routes/` directory
- Restart the dev server

### Type errors with routes
- Make sure routeTree.gen.ts is generated
- Check that the router is registered in main.tsx
- Verify route file exports use `export const Route`

### Authentication not working
- Check that token is being saved in authStore
- Verify HTTP client interceptors are configured
- Check browser localStorage for 'auth-storage' key

## Best Practices

1. **Route Definition**: Always use `createFileRoute` for type safety
2. **Navigation**: Use typed navigation with `navigate({ to: '...' })`
3. **Search Params**: Define validation in route files with `validateSearch`
4. **State Management**: Use Zustand for global state, React Query for server state
5. **HTTP Requests**: Always use the configured httpClient from `@/lib/httpClient`
6. **Styling**: Use the `cn()` utility for conditional and merged classNames
7. **Error Handling**: Leverage HTTP client interceptors for global error handling

## Next Steps

1. Add shadcn/ui components as needed
2. Implement protected routes using TanStack Router's `beforeLoad`
3. Add error boundaries for better error handling
4. Implement route-based code splitting
5. Add loading states with React Suspense
6. Configure React Query DevTools for development

## Resources

- [TanStack Router Documentation](https://tanstack.com/router)
- [Zustand Documentation](https://docs.pmnd.rs/zustand)
- [TanStack Query Documentation](https://tanstack.com/query)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Axios Documentation](https://axios-http.com)
