import type { Hazard } from '@/types/hazard';

export type HazardStreamPayload = {
  snapshot?: Hazard[];
  delta?: Hazard;
};

export function normalizeHazardRecord(value: unknown): Hazard | null {
  if (!value || typeof value !== 'object') {
    return null;
  }

  const hazard = value as Partial<Hazard> & { _id?: unknown };
  const normalizedId =
    typeof hazard.id === 'string' ? hazard.id : typeof hazard._id === 'string' ? hazard._id : null;

  if (
    !normalizedId ||
    typeof hazard.hazard_id !== 'string' ||
    typeof hazard.title !== 'string' ||
    typeof hazard.is_active !== 'boolean'
  ) {
    return null;
  }

  return {
    ...(hazard as Hazard),
    id: normalizedId,
    hazard_id: hazard.hazard_id,
    title: hazard.title,
    is_active: hazard.is_active,
  };
}

export function parseHazardStreamPayload(raw: string): HazardStreamPayload | null {
  let parsed: unknown;

  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }

  const getSnapshot = (value: unknown): Hazard[] | null => {
    if (!Array.isArray(value)) {
      return null;
    }

    return value
      .map((entry) => normalizeHazardRecord(entry))
      .filter((entry): entry is Hazard => entry !== null);
  };

  const directSnapshot = getSnapshot(parsed);
  if (directSnapshot !== null) {
    return { snapshot: directSnapshot };
  }

  const directDelta = normalizeHazardRecord(parsed);
  if (directDelta) {
    return { delta: directDelta };
  }

  if (!parsed || typeof parsed !== 'object') {
    return null;
  }

  const envelope = parsed as Record<string, unknown>;
  const envelopeSnapshot =
    getSnapshot(envelope.items) ??
    getSnapshot(envelope.hazards) ??
    getSnapshot(envelope.data) ??
    getSnapshot(envelope.payload);

  if (envelopeSnapshot !== null) {
    return { snapshot: envelopeSnapshot };
  }

  const envelopeDelta =
    normalizeHazardRecord(envelope.hazard) ??
    normalizeHazardRecord(envelope.data) ??
    normalizeHazardRecord(envelope.payload);

  if (envelopeDelta) {
    return { delta: envelopeDelta };
  }

  return null;
}