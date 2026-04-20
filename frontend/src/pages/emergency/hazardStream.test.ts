import { describe, expect, it } from 'vitest';

import { parseHazardStreamPayload } from './hazardStream';

function buildHazard(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'haz-1',
    hazard_id: 'HZ-001',
    title: 'Ngap lut tai Hai Chau',
    description: 'Muc nuoc dang tang',
    event_type: 'flood',
    severity: 'high',
    source: 'manual',
    is_active: true,
    geometry: { type: 'Point', coordinates: [108.22, 16.07] },
    metadata: {},
    created_at: '2026-04-19T09:00:00.000Z',
    updated_at: '2026-04-19T09:00:00.000Z',
    ...overrides,
  };
}

describe('parseHazardStreamPayload', () => {
  it('handles raw hazard object', () => {
    const payload = parseHazardStreamPayload(JSON.stringify(buildHazard()));

    expect(payload).toEqual({
      delta: expect.objectContaining({
        id: 'haz-1',
        hazard_id: 'HZ-001',
        title: 'Ngap lut tai Hai Chau',
        is_active: true,
      }),
    });
  });

  it('handles envelope with items array', () => {
    const payload = parseHazardStreamPayload(
      JSON.stringify({
        items: [buildHazard({ id: 'haz-2', hazard_id: 'HZ-002' })],
      })
    );

    expect(payload).toEqual({
      snapshot: [
        expect.objectContaining({
          id: 'haz-2',
          hazard_id: 'HZ-002',
          is_active: true,
        }),
      ],
    });
  });

  it.each(['hazards', 'data', 'payload'] as const)(
    'handles envelope with %s array',
    (field) => {
      const payload = parseHazardStreamPayload(
        JSON.stringify({
          [field]: [buildHazard({ id: `haz-${field}`, hazard_id: `HZ-${field.toUpperCase()}` })],
        })
      );

      expect(payload).toEqual({
        snapshot: [
          expect.objectContaining({
            id: `haz-${field}`,
            hazard_id: `HZ-${field.toUpperCase()}`,
            is_active: true,
          }),
        ],
      });
    }
  );

  it.each(['hazard', 'data', 'payload'] as const)(
    'handles envelope with %s object as delta',
    (field) => {
      const payload = parseHazardStreamPayload(
        JSON.stringify({
          [field]: buildHazard({ id: `delta-${field}`, hazard_id: `DELTA-${field.toUpperCase()}` }),
        })
      );

      expect(payload).toEqual({
        delta: expect.objectContaining({
          id: `delta-${field}`,
          hazard_id: `DELTA-${field.toUpperCase()}`,
          is_active: true,
        }),
      });
    }
  );

  it('keeps valid snapshot entries when mixed with invalid entries', () => {
    const payload = parseHazardStreamPayload(
      JSON.stringify({
        hazards: [
          buildHazard({ id: 'haz-valid-1', hazard_id: 'HZ-VALID-1' }),
          { hazard_id: 'HZ-INVALID-MISSING-ID' },
          buildHazard({ id: 'haz-valid-2', hazard_id: 'HZ-VALID-2' }),
          { id: 'haz-invalid-active', hazard_id: 'HZ-INVALID-ACTIVE', title: 'bad', is_active: 'yes' },
          null,
        ],
      })
    );

    expect(payload).toEqual({
      snapshot: [
        expect.objectContaining({ id: 'haz-valid-1', hazard_id: 'HZ-VALID-1' }),
        expect.objectContaining({ id: 'haz-valid-2', hazard_id: 'HZ-VALID-2' }),
      ],
    });
  });

  it('normalizes _id to id', () => {
    const payload = parseHazardStreamPayload(
      JSON.stringify(buildHazard({ id: undefined, _id: 'mongo-id-1', hazard_id: 'HZ-003' }))
    );

    expect(payload).toEqual({
      delta: expect.objectContaining({
        id: 'mongo-id-1',
        hazard_id: 'HZ-003',
      }),
    });
  });

  it('ignores invalid payload', () => {
    const invalidMissingFields = parseHazardStreamPayload(JSON.stringify({ hazard_id: 'HZ-004' }));
    const invalidJson = parseHazardStreamPayload('{bad json');

    expect(invalidMissingFields).toBeNull();
    expect(invalidJson).toBeNull();
  });
});