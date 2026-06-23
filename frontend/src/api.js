// API client for the SkyPath backend.
//
// The base URL comes from VITE_API_BASE_URL (injected by docker-compose) and
// falls back to localhost for local development.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Search itineraries between two airports on a date.
// TODO (step 5): handle non-OK responses (validation/empty/errors) and map
// the payload into the shape the results view expects.
export async function searchItineraries({ origin, destination, date }) {
  const params = new URLSearchParams({ origin, destination, date });
  const res = await fetch(`${BASE_URL}/search?${params}`);
  return res.json();
}
