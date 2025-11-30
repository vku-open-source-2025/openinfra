# OpenInfra Frontend

Modern React application for infrastructure management and monitoring, built with cutting-edge technologies for optimal performance and developer experience.

## Tech Stack

### Core
- **React 19.2** - Latest React with modern features
- **TypeScript 5.9** - Type-safe JavaScript
- **Vite 7.2** - Lightning-fast build tool

### Routing & Navigation
- **TanStack Router 1.139** - Type-safe, file-based routing
  - Auto-generated route tree
  - Built-in code splitting
  - Type-safe navigation and params
  - Route devtools in development

### State Management
- **Zustand 5.0** - Lightweight state management
  - Minimal boilerplate
  - TypeScript support
  - Persistence middleware
  - No context providers needed

### Data Fetching
- **TanStack Query 5.90** - Powerful async state management
  - Smart caching
  - Automatic refetching
  - Optimistic updates
  - Query devtools

### HTTP Client
- **Axios 1.13** - Enhanced HTTP client
  - Request/response interceptors
  - Automatic auth token injection
  - Centralized error handling
  - Configurable timeouts

### Styling
- **Tailwind CSS 4.1** - Utility-first CSS framework
- **clsx** - Conditional className utility
- **tailwind-merge** - Merge Tailwind classes efficiently
- **shadcn/ui** (configured) - Beautiful component system

### Maps & Visualization
- **Leaflet 1.9** - Interactive maps
- **React Leaflet 5.0** - React bindings for Leaflet
- **Leaflet Draw** - Drawing tools for maps
- **Leaflet Heat** - Heatmap visualization

### UI Components & Icons
- **Lucide React** - Beautiful icon library
- **Font Awesome** - Additional icons
- **React QR Code** - QR code generation

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui components
│   ├── Header.tsx
│   ├── Map.tsx
│   └── ...
├── pages/              # Page components
│   ├── HomePage.tsx
│   ├── PublicMap.tsx
│   └── Dashboard.tsx
├── routes/             # TanStack Router routes
│   ├── __root.tsx     # Root layout
│   ├── index.tsx      # Home route
│   ├── map.tsx        # Map route
│   └── admin.tsx      # Admin route
├── stores/             # Zustand stores
│   ├── authStore.ts   # Authentication state
│   ├── appStore.ts    # Application state
│   └── index.ts
├── lib/                # Utilities and configurations
│   ├── httpClient.ts  # Axios configuration
│   ├── queryClient.ts # TanStack Query config
│   └── utils.ts       # Helper functions (cn, etc.)
├── hooks/              # Custom React hooks
├── utils/              # Utility functions
├── api.ts              # API functions
├── main.tsx            # Application entry point
└── routeTree.gen.ts    # Auto-generated (don't edit)
```

## Getting Started

### Prerequisites
- Node.js 20.19+ or 22.12+
- pnpm (recommended) or npm

### Installation

```bash
# Install dependencies
pnpm install

# Start development server
pnpm run dev

# Build for production
pnpm run build

# Preview production build
pnpm run preview

# Lint code
pnpm run lint
```

### Environment Variables

Create a `.env` file in the root directory:

```env
VITE_BASE_API_URL=http://localhost:8000/api
VITE_LEADERBOARD_URL=https://contribapi.openinfra.space/api
```

## Key Features

### Type-Safe Routing
Routes are defined using file-based routing with full TypeScript support:

```tsx
// src/routes/map.tsx
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/map')({
  component: MapPage,
  validateSearch: (search) => ({
    assetId: search.assetId as string | undefined,
  }),
});
```

### State Management
Simple and powerful state management with Zustand:

```tsx
import { useAuthStore } from '@/stores';

function Component() {
  const { user, login, logout } = useAuthStore();
  // Authentication state with persistence
}
```

### Data Fetching
Efficient data fetching with TanStack Query:

```tsx
const { data, isLoading } = useQuery({
  queryKey: ['assets'],
  queryFn: getAssets,
});
```

### HTTP Client
Configured Axios client with interceptors:

```tsx
import { httpClient } from '@/lib/httpClient';

// Automatic auth token injection
// Centralized error handling
// 401 auto-logout
const response = await httpClient.get('/assets/');
```

## Adding shadcn/ui Components

The project is pre-configured for shadcn/ui. Add components as needed:

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
```

## Development

### Creating a New Route

1. Create a file in `src/routes/`:
```tsx
// src/routes/about.tsx
export const Route = createFileRoute('/about')({
  component: AboutPage,
});
```

2. The route is automatically available at `/about`

### Navigation

```tsx
import { Link, useNavigate } from '@tanstack/react-router';

// Declarative
<Link to="/map">Go to Map</Link>

// Programmatic
const navigate = useNavigate();
navigate({ to: '/admin' });
```

### Making API Calls

```tsx
// Always use the configured httpClient
import { httpClient } from '@/lib/httpClient';

const response = await httpClient.get('/assets/');
const data = response.data;
```

## Migration from React Router

See [MIGRATION.md](./MIGRATION.md) for detailed migration guide from React Router DOM to TanStack Router.

## Quick Reference

See [QUICK_START.md](./QUICK_START.md) for common patterns and examples.

## Build Configuration

### Vite Configuration
- TanStack Router plugin for route generation
- Path aliases (`@/` → `src/`)
- React Fast Refresh
- Auto-reload on changes

### TypeScript Configuration
- Strict mode enabled
- Path aliases configured
- ESM module system
- React JSX transform

## Performance Features

- Route-based code splitting
- Optimistic UI updates
- Smart query caching (5min stale time)
- Request deduplication
- Automatic retry with exponential backoff
- Window focus refetching

## Development Tools

Available in development mode:
- TanStack Router DevTools
- TanStack Query DevTools (to be enabled)
- React DevTools (browser extension)

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2022 features
- CSS Grid and Flexbox

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new code
3. Use the configured httpClient for API calls
4. Use Zustand for global state, React Query for server state
5. Add types for all components and functions
6. Test your changes locally

## Documentation

- [MIGRATION.md](./MIGRATION.md) - Tech stack migration guide
- [QUICK_START.md](./QUICK_START.md) - Quick reference and examples
- [TanStack Router Docs](https://tanstack.com/router)
- [Zustand Docs](https://docs.pmnd.rs/zustand)
- [TanStack Query Docs](https://tanstack.com/query)
- [shadcn/ui Docs](https://ui.shadcn.com)

## License

MIT
