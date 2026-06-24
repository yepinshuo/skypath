// Small presentation helpers. Times from the API are local ISO strings
// (e.g. "2024-03-15T08:30:00"); we render them as the traveler would read
// them on a board, and surface day rollovers explicitly.

// 375 -> "6h 15m", 45 -> "45m"
export function formatDuration(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

// "2024-03-15T08:30:00" -> "08:30"
export function formatClock(iso) {
  return iso.slice(11, 16);
}

// Whole-day difference between two local ISO dates (ignores clock time),
// used to badge arrivals that land on a later calendar day (+1, +2...).
export function dayOffset(baseIso, iso) {
  const base = new Date(baseIso.slice(0, 10) + "T00:00:00");
  const day = new Date(iso.slice(0, 10) + "T00:00:00");
  return Math.round((day - base) / 86400000);
}
