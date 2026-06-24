# SkyPath — Flight Connection Search Engine

> Prototype flight connection search engine. **Work in progress** — this README
> is a placeholder and will be filled in last (architecture, tradeoffs, and
> "what I'd improve" reflections written once the project is complete).

## Run

```bash
docker-compose up
```

- Backend (FastAPI): http://localhost:8000 — health check at `/health`
- Frontend (Vite/React): http://localhost:5173

## API

Single search endpoint, plus a health check.

```
GET /search?origin=JFK&destination=LAX&date=2024-03-15
GET /health
```

**Validation and error semantics** (the spec asks for graceful handling):

- `origin` / `destination` are normalized to uppercase and must be 3-letter
  IATA codes — malformed codes return **400** with a clear message.
- `date` must be ISO 8601 `YYYY-MM-DD` — anything else returns **400**.
- Origin equal to destination returns **400**. The spec allowed either an empty
  result or a validation error here; a 400 was chosen because it tells the user
  *why* nothing came back instead of looking like "no flights."
- An unknown (but well-formed) airport code returns **404** — a well-formed code
  that doesn't exist is a missing resource, distinct from malformed input.
- A valid route with no available itineraries returns **200** with an empty
  list, which the frontend renders as an empty state (distinct from an error).

Errors use FastAPI's standard `{"detail": "..."}` shape so the frontend can
display the message directly.

## Frontend

React + Vite single-page app that talks to the `/search` endpoint.

**Visual direction.** A "modern timetable": deep navy ink on cool paper with one
marigold accent, Space Grotesk for signage and airport codes, Inter with tabular
numerals for timetable-aligned data. Deliberately avoids the warm-cream/serif
look so it reads as a purpose-built travel tool.

**Signature element — the route strip.** Each itinerary is drawn as its airport
codes joined by flight legs, with an amber layover bead at every stop, so direct
vs. 1-stop vs. 2-stop is legible at a glance. A compact segment list underneath
carries the full detail the spec asks for (each leg's flight number, times,
airports, duration, price, and the layover between legs).

**The four required states.** Client-side validation blocks malformed searches
with field-level messages before any request goes out (3-letter codes,
origin ≠ destination, date required); a shimmer skeleton covers loading; the
empty state explains *why* nothing matched and suggests a next step; API errors
surface the backend's `detail` message verbatim. Server-side validation still
runs regardless, so the two layers agree.

**Day rollovers.** Arrivals that land on a later calendar day than the first
departure get a `+1`/`+2` badge, which is what makes the SYD→LAX date-line and
overnight connections readable.

**Notes.** The form pre-fills `JFK → LAX` on `2024-03-15` so the tool returns
results on first load (the dataset only covers that date). The backend base URL
comes from `VITE_API_BASE_URL` (set by docker-compose), falling back to
localhost for local dev.

## Search & connection logic

How itineraries are found and which judgment calls were made on ambiguous rules.

**Algorithm.** The schedule is treated as a time-expanded graph. From each
first-leg flight that departs the origin on the requested date, a depth-first
expansion adds up to two connections (max 2 stops / 3 segments). Each candidate
connection is validated against the layover rules *before* recursing, so invalid
branches are pruned early. With ~300 flights this is comfortably fast; no
indexing beyond flights-by-origin was needed.

**All durations are timezone-aware.** Dataset times are naive local strings, so
every flight's departure/arrival is localized with its airport's IANA timezone
before any arithmetic. Segment duration, layover, and total travel time are all
computed on these real instants — e.g. JFK→LAX is 6h15m of real travel despite
looking like ~3h in raw local time, and the SYD→LAX date-line flight that
"arrives before it departs" in local time correctly comes out as 15h.

**Domestic vs international connection.** The spec defines a connection as
domestic when both the arriving and departing flights are within the same
country. Since both flights share the connection airport, this is implemented as
"origin of the arriving flight, the connection airport, and destination of the
departing flight are all in the same country." A US→US arrival followed by a
US→international departure is therefore treated as international (90-min minimum),
which matches the intent that the *departure* out of the connection matters.

**Date applies to the first leg only.** The requested date constrains the first
flight's local departure date. Connecting flights may roll past midnight — an
overnight layover is valid as long as it satisfies the min/max layover rules.
This is what lets legitimate red-eye connections appear in results.

**No revisiting airports.** A path never returns to an airport it has already
visited, which prevents nonsensical loops (e.g. A→B→A→C) and bounds the search.

**Result ordering.** Sorted by total travel time (shortest first) as required,
tie-broken by total price then number of stops for stable, sensible ordering.

**Airport changes during a layover** (e.g. JFK→LGA) are impossible by
construction: a connection only extends via flights departing the exact airport
the previous flight landed at.

## Data handling decisions

The dataset (`flights.json`) contains a few intentional quirks. These are the
decisions made while loading it, recorded here as we go so the rationale isn't
lost. (Notably, the `SP995` row combines two quirks at once — a typo'd origin
*and* a string price — so it exercises both of the first two decisions below.)

### Bad rows are skipped and logged, not fatal

A row that can't be parsed or resolved is skipped, logged, and counted (surfaced
in the startup summary), rather than aborting the whole load.

- **Why:** for a prototype ingesting a fixed dataset, one bad row shouldn't take
  down the service; this also directly addresses the "handle data quirks
  gracefully" goal.
- **Tradeoff:** skipping can mask upstream data problems. A stricter
  fail-fast-on-bad-data mode would catch those earlier; that's a reasonable
  alternative if this were a real ingestion pipeline.

### Airport-code typos are corrected when unambiguous

One flight has origin `JKF`, which isn't a real airport. Instead of dropping it,
an unknown code is corrected to a known one **when its letters are an
unambiguous transposition** of exactly one known code (`JKF` → `JFK`). The
corrected code is persisted on the flight so search and the API see canonical
IATA codes.

- **Why:** `JKF` is clearly a transposed `JFK`. A general "single same-letter
  match" rule reads better than a hardcoded `{"JKF": "JFK"}` map and handles
  similar typos.
- **Safety:** correction only happens when exactly one known code matches, so a
  genuinely invalid code like `XXX` is left unresolved (and the row skipped) —
  this keeps the invalid-airport test case intact. Verified there are no
  same-letter collisions among the 25 airport codes.
- **Tradeoff:** a heuristic could in theory mis-correct on a larger/looser
  dataset; the hardcoded-map alternative is simpler but less general.

### Mixed price types are coerced to float explicitly

Most prices are numbers, but a few rows store price as a string (e.g. `"289.00"`,
`"99"`). A `price` validator on the `Flight` model coerces these to float.

- **Why:** done explicitly (rather than relying on Pydantic's implicit
  coercion) so the behavior is intentional, self-documenting, and survives if
  the model is ever switched to strict mode.
- **Tradeoff:** a value that can't be parsed as a number (e.g. `"free"`) raises a
  validation error and that row is skipped, consistent with the bad-row policy
  above.

## Tests

The backend ships a pytest suite covering the six test cases from the
instructions (`backend/tests/`), exercised through the HTTP endpoint so they
also cover request validation and the response shape. The tests read the dataset
independently of the app to check connection rules (e.g. the domestic vs.
international layover minimum) rather than trusting the code under test.

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## Status

Feature-complete prototype: the timezone-aware dataset loader (with the
data-handling decisions above), the connection-search algorithm, the validated
`/search` endpoint, and the React frontend (search form, route-strip results,
and the loading / empty / error / validation states). Backend verified against
all six instruction test cases, an exhaustive all-pairs invariant sweep, and
full endpoint error-path coverage; the frontend builds clean and its rendering
logic is checked against live API responses. Remaining: a final polish pass and
expanding this README into the full architecture / tradeoffs / "what I'd improve"
write-up.
