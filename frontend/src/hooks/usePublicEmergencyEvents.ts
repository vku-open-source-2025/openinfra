import { useQuery } from '@tanstack/react-query';
import { emergencyApi } from '../api/emergency';
import type { PublicEmergencyEvent } from '../types/emergency';

export function usePublicEmergencyEvents(enabled = true, limit = 50) {
  return useQuery<PublicEmergencyEvent[]>({
    queryKey: ['emergency', 'public', limit],
    queryFn: () => emergencyApi.listPublic({ limit }),
    enabled,
    staleTime: 60_000,
    refetchInterval: 2 * 60_000,
  });
}
