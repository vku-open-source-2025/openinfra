import { describe, expect, it } from 'vitest';

import type { Hazard } from '../types/hazard';
import { filterHazardsInLastHours, getHazardTimestampMs } from './recentHazards';

const NOW_ISO = '2026-04-20T10:00:00.000Z';
const NOW_MS = Date.parse(NOW_ISO);

function buildHazard(overrides: Partial<Hazard> = {}): Hazard {
  return {
    id: 'hz-1',
    hazard_id: 'HZ-001',
    title: 'Ngap lut tai Da Nang',
    event_type: 'flood',
    severity: 'high',
    source: 'manual',
    is_active: true,
    geometry: { type: 'Point', coordinates: [108.22, 16.07] },
    metadata: {},
    created_at: '2026-04-20T06:00:00.000Z',
    updated_at: '2026-04-20T06:00:00.000Z',
    ...overrides,
  };
}

describe('getHazardTimestampMs', () => {
  it('prefers detected_at when present', () => {
    const hazard = buildHazard({
      detected_at: '2026-04-20T08:30:00.000Z',
      created_at: '2026-04-20T05:00:00.000Z',
    });

    expect(getHazardTimestampMs(hazard)).toBe(Date.parse('2026-04-20T08:30:00.000Z'));
  });

  it('falls back to created_at when optional timestamps are missing', () => {
    const hazard = buildHazard({
      detected_at: undefined,
      issued_at: undefined,
      ingest_timestamp: undefined,
      created_at: '2026-04-20T03:00:00.000Z',
    });

    expect(getHazardTimestampMs(hazard)).toBe(Date.parse('2026-04-20T03:00:00.000Z'));
  });
});

describe('filterHazardsInLastHours', () => {
  it('keeps only hazards inside the configured recent window', () => {
    const hazards = [
      buildHazard({ id: 'inside-1', created_at: '2026-04-20T09:00:00.000Z' }),
      buildHazard({ id: 'inside-2', created_at: '2026-04-19T14:30:00.000Z' }),
      buildHazard({ id: 'outside-1', created_at: '2026-04-19T08:59:59.000Z' }),
    ];

    const recent = filterHazardsInLastHours(hazards, 24, NOW_MS);

    expect(recent.map((hazard) => hazard.id)).toEqual(['inside-1', 'inside-2']);
  });

  it('sorts by newest hazard timestamp first', () => {
    const hazards = [
      buildHazard({ id: 'older', created_at: '2026-04-20T02:00:00.000Z' }),
      buildHazard({ id: 'newer', created_at: '2026-04-20T09:30:00.000Z' }),
      buildHazard({ id: 'middle', created_at: '2026-04-20T06:45:00.000Z' }),
    ];

    const recent = filterHazardsInLastHours(hazards, 24, NOW_MS);

    expect(recent.map((hazard) => hazard.id)).toEqual(['newer', 'middle', 'older']);
  });
});