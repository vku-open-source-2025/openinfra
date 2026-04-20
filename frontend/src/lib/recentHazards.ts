import type { Hazard } from '../types/hazard';

const HOUR_IN_MS = 60 * 60 * 1000;
const TIMESTAMP_FIELDS = [
  'detected_at',
  'issued_at',
  'ingest_timestamp',
  'created_at',
  'updated_at',
] as const;

export function getHazardTimestampMs(hazard: Hazard): number | null {
  for (const field of TIMESTAMP_FIELDS) {
    const value = hazard[field];
    if (typeof value !== 'string' || value.length === 0) {
      continue;
    }

    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }

  return null;
}

export function filterHazardsInLastHours(
  hazards: Hazard[],
  hours: number,
  nowMs: number = Date.now()
): Hazard[] {
  const safeHours = Number.isFinite(hours) ? Math.max(1, Math.floor(hours)) : 24;
  const cutoffMs = nowMs - safeHours * HOUR_IN_MS;

  return hazards
    .map((hazard) => ({
      hazard,
      timestampMs: getHazardTimestampMs(hazard),
    }))
    .filter((entry) => entry.timestampMs !== null && entry.timestampMs >= cutoffMs)
    .sort((left, right) => {
      const leftTimestamp = left.timestampMs ?? 0;
      const rightTimestamp = right.timestampMs ?? 0;
      return rightTimestamp - leftTimestamp;
    })
    .map((entry) => entry.hazard);
}