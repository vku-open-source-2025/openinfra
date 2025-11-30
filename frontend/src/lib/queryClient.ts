import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: 5 minutes (data considered fresh for 5 minutes)
      staleTime: 5 * 60 * 1000,

      // Cache time: 10 minutes (unused data removed from cache after 10 minutes)
      gcTime: 10 * 60 * 1000,

      // Retry failed requests 3 times with exponential backoff
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Refetch on window focus for better UX
      refetchOnWindowFocus: true,

      // Don't refetch on mount if data is still fresh
      refetchOnMount: false,

      // Refetch on reconnect
      refetchOnReconnect: true,

      // Don't throw errors to error boundaries by default
      throwOnError: false,
    },
    mutations: {
      // Retry mutations once on failure
      retry: 1,

      // Throw errors from mutations to error boundaries
      throwOnError: false,

      // Error handler for mutations
      onError: (error) => {
        console.error('Mutation error:', error);
      },
    },
  },
});
