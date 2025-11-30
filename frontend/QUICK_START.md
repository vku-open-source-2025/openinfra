# Quick Start Guide - Updated Tech Stack

## Quick Reference

### Creating a New Route

1. Create a file in `src/routes/`:
```tsx
// src/routes/about.tsx
import { createFileRoute } from '@tanstack/react-router';
import AboutPage from '../pages/AboutPage';

export const Route = createFileRoute('/about')({
  component: AboutPage,
});
```

2. The route will be automatically available at `/about`

### Navigation

```tsx
import { Link, useNavigate } from '@tanstack/react-router';

// Using Link
<Link to="/map">Go to Map</Link>
<Link to="/map" search={{ assetId: '123' }}>View Asset</Link>

// Using programmatic navigation
const navigate = useNavigate();
navigate({ to: '/admin' });
navigate({ to: '/map', search: { assetId: asset._id } });
```

### Using Zustand Store

```tsx
import { useAuthStore } from '@/stores';

function Component() {
  const { user, token, login, logout } = useAuthStore();

  // Login
  login('token-here', { id: '1', email: 'user@example.com', name: 'User' });

  // Logout
  logout();

  // Check authentication
  if (user) {
    // User is logged in
  }
}
```

### Making HTTP Requests

```tsx
import { httpClient } from '@/lib/httpClient';

// GET request
const response = await httpClient.get('/assets/');
const assets = response.data;

// POST request
const response = await httpClient.post('/maintenance/', {
  asset_id: '123',
  description: 'Fix leak',
});

// The token is automatically added to headers if user is authenticated
```

### Using TanStack Query

```tsx
import { useQuery, useMutation } from '@tanstack/react-query';
import { getAssets, createAsset } from '@/api';

// Fetch data
const { data, isLoading, error } = useQuery({
  queryKey: ['assets'],
  queryFn: getAssets,
});

// Mutate data
const mutation = useMutation({
  mutationFn: createAsset,
  onSuccess: () => {
    // Invalidate and refetch
    queryClient.invalidateQueries({ queryKey: ['assets'] });
  },
});
```

### Using the cn() Utility

```tsx
import { cn } from '@/lib/utils';

<div className={cn(
  'base-class',
  'p-4',
  isActive && 'bg-blue-500',
  error && 'border-red-500'
)} />
```

### Search Params (Type-safe)

1. Define validation in route file:
```tsx
// src/routes/map.tsx
export const Route = createFileRoute('/map')({
  component: PublicMap,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      assetId: search.assetId as string | undefined,
      view: search.view as 'list' | 'grid' | undefined,
    };
  },
});
```

2. Use in component:
```tsx
import { useSearch, useNavigate } from '@tanstack/react-router';

const searchParams = useSearch({ from: '/map' });
const assetId = searchParams?.assetId;
const view = searchParams?.view || 'list';

const navigate = useNavigate();
navigate({
  to: '/map',
  search: { assetId: '123', view: 'grid' }
});
```

### Protected Routes

```tsx
// src/routes/admin.tsx
import { createFileRoute, redirect } from '@tanstack/react-router';
import { useAuthStore } from '@/stores';

export const Route = createFileRoute('/admin')({
  beforeLoad: () => {
    const { isAuthenticated } = useAuthStore.getState();
    if (!isAuthenticated) {
      throw redirect({ to: '/' });
    }
  },
  component: Dashboard,
});
```

### Adding shadcn/ui Components

```bash
# Add a button component
npx shadcn@latest add button

# Add multiple components
npx shadcn@latest add button card dialog
```

Use the component:
```tsx
import { Button } from '@/components/ui/button';

<Button variant="default">Click me</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
```

## Common Patterns

### Loading States

```tsx
const { data, isLoading } = useQuery({
  queryKey: ['assets'],
  queryFn: getAssets,
});

if (isLoading) {
  return <div>Loading...</div>;
}

return <div>{/* render data */}</div>;
```

### Error Handling

```tsx
const { data, error } = useQuery({
  queryKey: ['assets'],
  queryFn: getAssets,
});

if (error) {
  return <div>Error: {error.message}</div>;
}
```

### Optimistic Updates

```tsx
const mutation = useMutation({
  mutationFn: updateAsset,
  onMutate: async (newAsset) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['assets'] });

    // Snapshot previous value
    const previousAssets = queryClient.getQueryData(['assets']);

    // Optimistically update
    queryClient.setQueryData(['assets'], (old) => [...old, newAsset]);

    // Return context with previous value
    return { previousAssets };
  },
  onError: (err, newAsset, context) => {
    // Rollback on error
    queryClient.setQueryData(['assets'], context.previousAssets);
  },
  onSettled: () => {
    // Always refetch after error or success
    queryClient.invalidateQueries({ queryKey: ['assets'] });
  },
});
```

### Combining Multiple Stores

```tsx
import { useAuthStore, useAppStore } from '@/stores';

function Component() {
  const user = useAuthStore((state) => state.user);
  const theme = useAppStore((state) => state.theme);
  const setTheme = useAppStore((state) => state.setTheme);

  return (
    <div>
      <p>User: {user?.name}</p>
      <p>Theme: {theme}</p>
      <button onClick={() => setTheme('dark')}>Dark Mode</button>
    </div>
  );
}
```

## File Structure for New Features

When adding a new feature:

```
src/
├── routes/
│   └── feature.tsx          # Route definition
├── pages/
│   └── FeaturePage.tsx      # Page component
├── components/
│   └── FeatureComponent.tsx # Reusable components
├── stores/
│   └── featureStore.ts      # Feature-specific state (if needed)
├── hooks/
│   └── useFeature.ts        # Custom hooks
└── api.ts                   # Add API functions
```

## Environment Variables

```env
# .env
VITE_BASE_API_URL=http://localhost:8000/api
VITE_LEADERBOARD_URL=https://contribapi.openinfra.space/api
```

Access in code:
```tsx
import.meta.env.VITE_BASE_API_URL
```

## Development Commands

```bash
# Start dev server
pnpm run dev

# Build for production
pnpm run build

# Preview production build
pnpm run preview

# Lint code
pnpm run lint
```

## Tips

1. **Always use path aliases**: `import { cn } from '@/lib/utils'` instead of `'../../lib/utils'`
2. **Keep routes simple**: Use route files only for route config, put logic in page components
3. **Use the stores wisely**: Auth and app-wide state in Zustand, server state in React Query
4. **Type everything**: Leverage TypeScript for better DX and fewer bugs
5. **Lazy load routes**: Routes are code-split by default, no need to manually lazy load
6. **Use devtools**: TanStack Router and Query devtools are available in development

## Common Issues

### "Cannot find module '@/...'"
- Make sure vite.config.ts has the path alias configured
- Restart the TypeScript server in your IDE

### Routes not updating
- Check that the route file exports `export const Route`
- Restart the dev server to regenerate route tree

### Authentication not persisting
- Check browser localStorage for 'auth-storage'
- Verify persist middleware is configured in authStore

### Type errors with router
- Ensure routeTree.gen.ts is generated
- Make sure router is registered in main.tsx with proper types
