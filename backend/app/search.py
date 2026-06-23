"""Itinerary search.

`search_itineraries` is the single entry point the API calls. It expands valid
journeys from origin to destination on a given date, honoring the SkyPath
connection rules (min/max layover, no airport changes, max 2 stops) and the
timezone-aware duration math.

NOTE (skeleton): the algorithm is stubbed and lands in step 3. The signature and
the intended approach are documented here so the API layer can be wired against
a stable contract.
"""

from __future__ import annotations

from datetime import date as Date

from .data import FlightRepository
from .models import Itinerary


def search_itineraries(
    repo: FlightRepository,
    origin: str,
    destination: str,
    date: Date,
) -> list[Itinerary]:
    """Return all valid itineraries from `origin` to `destination` on `date`.

    Intended approach (step 3):
      * Treat the schedule as a time-expanded graph. Starting from flights that
        depart `origin` on `date`, perform a bounded depth-first expansion of up
        to MAX_STOPS connections.
      * At each connection, attach the airports' timezones to the arrival and
        the next departure, compute the real layover, and keep the connection
        only if it satisfies:
          - same airport (no JFK->LGA changes)
          - min layover (domestic vs international, by airport country)
          - max layover
      * Compute each segment's real duration and each itinerary's total
        duration / total price using timezone-aware instants.
      * Sort the results by total travel time (shortest first).

    The skeleton returns an empty list; callers should treat that as
    "not yet implemented".
    """
    raise NotImplementedError("search_itineraries is implemented in step 3")
