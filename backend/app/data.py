"""Dataset loading and in-memory access.

`FlightRepository` owns the parsed dataset and the lookup structures the search
algorithm relies on (airport-by-code, flights-by-origin). It is loaded once at
startup and treated as read-only thereafter.

Loading is defensive about messy data. The dataset includes a flight whose
origin is the typo `JKF`: rather than dropping it, we correct unambiguous
letter-transposition typos to the matching known airport (`JFK`). Rows that
still can't be resolved, or that fail validation, are skipped and counted so a
single bad row can't crash the service.
"""

from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from .models import Airport, Flight

logger = logging.getLogger("skypath")


class FlightRepository:
    """In-memory store for airports and flights with lookup indexes."""

    def __init__(self) -> None:
        self._airports: dict[str, Airport] = {}
        # Flights keyed by origin airport code for fast connection expansion.
        self._flights_by_origin: dict[str, list[Flight]] = {}
        # Count of rows skipped during the last load (bad/unknown data).
        self._skipped: int = 0

    def load(self, path: str) -> None:
        """Read the dataset from `path` and build lookup indexes.

        Airports are indexed by IATA code; flights are indexed by origin. Any
        flight that fails validation or references an airport not present in the
        dataset is skipped (and logged), so a single bad row can't take down the
        whole service.
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self._airports = self._index_airports(raw.get("airports", []))
        self._flights_by_origin, self._skipped = self._index_flights(
            raw.get("flights", []), self._airports
        )

        if self._skipped:
            logger.warning("Skipped %d flight(s) during load", self._skipped)

    @staticmethod
    def _index_airports(rows: list[dict]) -> dict[str, Airport]:
        """Parse airport rows into models indexed by code (last write wins)."""
        airports: dict[str, Airport] = {}
        for row in rows:
            try:
                airport = Airport(**row)
            except ValidationError as exc:
                logger.warning("Skipping malformed airport row %r: %s", row, exc)
                continue
            if airport.code in airports:
                logger.warning("Duplicate airport code %s; overwriting", airport.code)
            airports[airport.code] = airport
        return airports

    @staticmethod
    def _resolve_code(code: str, airports: dict[str, Airport]) -> str | None:
        """Resolve an airport code, correcting simple transposition typos.

        Returns the code unchanged if it's already known. Otherwise, if exactly
        one known airport has the same set of letters (e.g. the dataset's `JKF`
        for `JFK`), returns that code. If there's no unambiguous match (e.g.
        `XXX`), returns None so the caller can skip the row. The single-match
        guard keeps us from silently "fixing" a genuinely unknown code.
        """
        if code in airports:
            return code
        signature = "".join(sorted(code))
        matches = [c for c in airports if "".join(sorted(c)) == signature]
        return matches[0] if len(matches) == 1 else None

    @classmethod
    def _index_flights(
        cls, rows: list[dict], airports: dict[str, Airport]
    ) -> tuple[dict[str, list[Flight]], int]:
        """Parse flight rows into models indexed by origin.

        Corrects simple airport-code typos where possible (see `_resolve_code`).
        Skips rows that fail validation or reference an unresolvable airport.
        Returns the index and the number skipped.
        """
        by_origin: dict[str, list[Flight]] = {}
        skipped = 0
        for row in rows:
            try:
                flight = Flight(**row)
            except ValidationError as exc:
                logger.warning("Skipping malformed flight row %r: %s", row, exc)
                skipped += 1
                continue

            origin = cls._resolve_code(flight.origin, airports)
            destination = cls._resolve_code(flight.destination, airports)
            if origin is None or destination is None:
                unknown = [
                    raw
                    for raw, resolved in (
                        (flight.origin, origin),
                        (flight.destination, destination),
                    )
                    if resolved is None
                ]
                logger.warning(
                    "Skipping flight %s: unresolvable airport(s) %s",
                    flight.flightNumber,
                    ", ".join(unknown),
                )
                skipped += 1
                continue

            # Persist any corrected codes so downstream/search see canonical IATA.
            if (origin, destination) != (flight.origin, flight.destination):
                logger.info(
                    "Corrected flight %s codes: %s->%s, %s->%s",
                    flight.flightNumber,
                    flight.origin,
                    origin,
                    flight.destination,
                    destination,
                )
                flight = flight.model_copy(update={"origin": origin, "destination": destination})

            by_origin.setdefault(origin, []).append(flight)
        return by_origin, skipped

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

    @property
    def skipped_count(self) -> int:
        return self._skipped


# Module-level singleton populated on startup (see main.py).
repository = FlightRepository()
