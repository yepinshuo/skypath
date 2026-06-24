// API client for the SkyPath backend.
//
// The base URL comes from VITE_API_BASE_URL (injected by docker-compose) and
// falls back to localhost for local development.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Thrown for any non-OK response so the UI can show the backend's message.
export class ApiError extends Error {}

// Search itineraries between two airports on a date.
// Resolves to the SearchResponse payload, or throws ApiError with a readable
// message (the backend's `detail`, or a network-level fallback).
export async function searchItineraries({ origin, destination, date }) {
  const params = new URLSearchParams({ origin, destination, date });
  let res;
  try {
    res = await fetch(`${BASE_URL}/search?${params}`);
  } catch {
    throw new ApiError("Can't reach the search service. Is the backend running?");
  }

  let body = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON response; handled below */
  }

  if (!res.ok) {
    const detail = body && body.detail ? body.detail : `Request failed (${res.status})`;
    throw new ApiError(detail);
  }
  return body;
}
