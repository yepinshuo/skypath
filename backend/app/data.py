"""Dataset loading and in-memory access.

`FlightRepository` owns the parsed dataset and the lookup structures the search
algorithm relies on (airport-by-code, flights-by-origin). It is loaded once at
startup and treated as read-only thereafter.

NOTE (skeleton): the parsing/indexing logic is stubbed out and lands in a later
commit. For now `load()` reads the file but builds empty indexes so the service
boots cleanly while the search endpoint reports "not implemented".
"""

from __future__ import annotations

import json

from .models import Airport, Flight


class FlightRepository:
    """In-memory store for airports and flights with lookup indexes."""

    def __init__(self) -> None:
        self._airports: dict[str, Airport] = {}
        # Flights keyed by origin airport code for fast connection expansion.
        self._flights_by_origin: dict[str, list[Flight]] = {}

    def load(self, path: str) -> None:
        """Read the dataset from `path` and build lookup indexes.

        TODO (step 2):
          * parse `airports` into Airport models, index by code
          * parse `flights` into Flight models, index by origin
          * validate that every flight references a known airport
        """
        with open(path, "r", encoding="utf-8") as f:
            _raw = json.load(f)  # noqa: F841  (parsing wired up in step 2)
        # Indexes intentionally left empty in the skeleton.
        self._airports = {}
        self._flights_by_origin = {}

    # --- Lookups (used by the search layer) ------------------------------

    def get_airport(self, code: str) -> Airport | None:
        """Return the airport for an IATA code, or None if unknown."""
        return self._airports.get(code)

    def flights_from(self, code: str) -> list[Flight]:
        """Return all flights departing from the given airport code."""
        return self._flights_by_origin.get(code, [])

    @property
    def airport_count(self) -> int:
        return len(self._airports)

    @property
    def flight_count(self) -> int:
        return sum(len(v) for v in self._flights_by_origin.values())


# Module-level singleton populated on startup (see main.py).
repository = FlightRepository()
