"""Itinerary search.

`search_itineraries` is the single entry point the API calls. It expands valid
journeys from origin to destination on a given date, honoring the SkyPath
connection rules (min/max layover, no airport changes, max 2 stops) and doing
all duration math in real (timezone-aware) time.

Approach: the schedule is treated as a time-expanded graph. Starting from
flights that depart `origin` on the requested date, we run a bounded
depth-first expansion of up to MAX_STOPS connections. Each candidate connection
is validated against the layover rules before we recurse, which prunes the
search early.
"""

from __future__ import annotations

from datetime import date as Date
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config
from .data import FlightRepository
from .models import Flight, FlightSegment, Itinerary, Layover

MAX_SEGMENTS = config.MAX_STOPS + 1  # 2 stops => up to 3 flight segments


# --- Timezone-aware helpers ----------------------------------------------


def _instant(local_iso: str, tz_name: str) -> datetime:
    """Attach an airport's timezone to a naive local ISO timestamp.

    Dataset times are naive strings in the local time of their airport, so we
    must localize them before any duration arithmetic is meaningful.
    """
    return datetime.fromisoformat(local_iso).replace(tzinfo=ZoneInfo(tz_name))


def _minutes(later: datetime, earlier: datetime) -> int:
    """Whole-minute difference between two aware datetimes."""
    return int((later - earlier).total_seconds() // 60)


class _Search:
    """Holds per-request context so the recursion stays readable.

    Caches airport timezone/country lookups and precomputes each flight's real
    departure/arrival instants, since the same flight can be visited many times
    across different candidate itineraries.
    """

    def __init__(self, repo: FlightRepository, destination: str) -> None:
        self.repo = repo
        self.destination = destination
        self._dep: dict[int, datetime] = {}
        self._arr: dict[int, datetime] = {}

    def _tz(self, code: str) -> str:
        return self.repo.get_airport(code).timezone

    def _country(self, code: str) -> str:
        return self.repo.get_airport(code).country

    def dep_instant(self, f: Flight) -> datetime:
        key = id(f)
        if key not in self._dep:
            self._dep[key] = _instant(f.departureTime, self._tz(f.origin))
        return self._dep[key]

    def arr_instant(self, f: Flight) -> datetime:
        key = id(f)
        if key not in self._arr:
            self._arr[key] = _instant(f.arrivalTime, self._tz(f.destination))
        return self._arr[key]

    def is_domestic_connection(self, arriving: Flight, departing: Flight) -> bool:
        """Domestic iff both flights stay within one country.

        Per the spec, a connection is domestic only when the arriving and
        departing flights are each within the same country. Because both flights
        share the connection airport, that's equivalent to: the arriving flight's
        origin, the connection airport, and the departing flight's destination
        are all in the same country.
        """
        return (
            self._country(arriving.origin)
            == self._country(arriving.destination)
            == self._country(departing.destination)
        )

    def connection_is_valid(self, arriving: Flight, departing: Flight) -> bool:
        """Check the layover between two consecutive flights against the rules."""
        layover = _minutes(self.dep_instant(departing), self.arr_instant(arriving))
        min_required = (
            config.MIN_LAYOVER_DOMESTIC_MINUTES
            if self.is_domestic_connection(arriving, departing)
            else config.MIN_LAYOVER_INTERNATIONAL_MINUTES
        )
        return min_required <= layover <= config.MAX_LAYOVER_MINUTES

    def build_itinerary(self, path: list[Flight]) -> Itinerary:
        """Assemble an Itinerary (segments, layovers, totals) from a flight path."""
        segments = [
            FlightSegment(
                flightNumber=f.flightNumber,
                airline=f.airline,
                origin=f.origin,
                destination=f.destination,
                departureTime=f.departureTime,
                arrivalTime=f.arrivalTime,
                durationMinutes=_minutes(self.arr_instant(f), self.dep_instant(f)),
                price=f.price,
            )
            for f in path
        ]
        layovers = [
            Layover(
                airport=prev.destination,
                durationMinutes=_minutes(
                    self.dep_instant(nxt), self.arr_instant(prev)
                ),
            )
            for prev, nxt in zip(path, path[1:])
        ]
        total_duration = _minutes(self.arr_instant(path[-1]), self.dep_instant(path[0]))
        total_price = round(sum(f.price for f in path), 2)
        return Itinerary(
            segments=segments,
            layovers=layovers,
            stops=len(path) - 1,
            totalDurationMinutes=total_duration,
            totalPrice=total_price,
        )

    def expand(self, path: list[Flight], visited: set[str], out: list[Itinerary]) -> None:
        """Depth-first extension of a partial path by one more flight."""
        if len(path) >= MAX_SEGMENTS:
            return
        last = path[-1]
        for nxt in self.repo.flights_from(last.destination):
            # Don't revisit an airport already on the path (no loops / backtracks).
            if nxt.destination in visited:
                continue
            if not self.connection_is_valid(last, nxt):
                continue
            extended = path + [nxt]
            if nxt.destination == self.destination:
                out.append(self.build_itinerary(extended))
            else:
                self.expand(extended, visited | {nxt.destination}, out)


def search_itineraries(
    repo: FlightRepository,
    origin: str,
    destination: str,
    date: Date,
) -> list[Itinerary]:
    """Return valid itineraries from `origin` to `destination` on `date`.

    The `date` constrains the *first* flight's local departure date; connecting
    flights may roll past midnight (an overnight layover is still valid as long
    as it satisfies the layover rules). Results are sorted by total travel time
    (shortest first), tie-broken by price then number of stops.
    """
    if origin == destination:
        return []
    if repo.get_airport(origin) is None or repo.get_airport(destination) is None:
        return []

    ctx = _Search(repo, destination)
    results: list[Itinerary] = []

    for first in repo.flights_from(origin):
        # First leg must depart on the requested date (local time at origin).
        if datetime.fromisoformat(first.departureTime).date() != date:
            continue
        if first.destination == destination:
            results.append(ctx.build_itinerary([first]))
        else:
            ctx.expand([first], {origin, first.destination}, results)

    results.sort(key=lambda it: (it.totalDurationMinutes, it.totalPrice, it.stops))
    return results
