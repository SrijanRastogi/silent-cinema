const MAX_HOURS = 999;

/** Render integer microseconds as ``HH:MM:SS.mmm``. */
export function formatTimecode(timestampUs: number): string {
  const safe = Math.max(0, Math.round(timestampUs));
  const milliseconds = Math.round(safe / 1000);
  const hours = Math.floor(milliseconds / 3_600_000);
  const minutes = Math.floor((milliseconds % 3_600_000) / 60_000);
  const seconds = Math.floor((milliseconds % 60_000) / 1000);
  const millis = milliseconds % 1000;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(
    seconds,
  ).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}

/**
 * Parse ``HH:MM:SS.mmm``, ``MM:SS.mmm``, or ``SS.mmm`` into integer
 * microseconds. Returns ``null`` for anything else; no guessing.
 */
export function parseTimecode(value: string): number | null {
  const parts = value.trim().split(":");
  if (parts.length === 0 || parts.length > 3) {
    return null;
  }
  const secondsPart = parts.at(-1) ?? "";
  if (!/^\d{1,2}(\.\d{1,3})?$/.test(secondsPart)) {
    return null;
  }
  const wholeParts = parts.slice(0, -1);
  if (wholeParts.some((part) => !/^\d{1,3}$/.test(part))) {
    return null;
  }
  if (parts.length === 3 && Number(parts[0]) > MAX_HOURS) {
    return null;
  }
  if (parts.length >= 2 && Number(parts.at(-2)) > 59) {
    return null;
  }

  const [secondsWhole, fraction = ""] = secondsPart.split(".");
  let totalSeconds = 0;
  for (const part of wholeParts) {
    totalSeconds = totalSeconds * 60 + Number(part);
  }
  const milliseconds = Number(fraction.padEnd(3, "0"));
  return totalSeconds * 1_000_000 + Number(secondsWhole) * 1_000_000 + milliseconds * 1000;
}

export function activeEntryIndex(
  entries: { start_us: number; end_us: number }[],
  positionUs: number,
): number {
  return entries.findIndex((entry) => entry.start_us <= positionUs && positionUs < entry.end_us);
}
