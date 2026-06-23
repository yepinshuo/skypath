"""Pydantic models for SkyPath.

Two groups of models live here:

* Domain models that mirror the raw dataset (`Airport`, `Flight`). These are
  what the repository loads and what the search algorithm reasons over.
* API response models (`FlightSegment`, `Layover`, `Itinerary`,
  `SearchResponse`) that describe the JSON we return to the frontend.

The split keeps the wire format decoupled from the storage format: the search
layer can carry around richer internal state while the API exposes only what
the client needs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Domain models (mirror flights.json) ---------------------------------


class Airport(BaseModel):
    """An airport as described in the dataset."""

    code: str = Field(..., description="3-letter IATA code, e.g. 'JFK'")
    name: str
    city: str
    country: str = Field(..., description="ISO country code, e.g. 'US'")
    timezone: str = Field(..., description="IANA tz name, e.g. 'America/New_York'")


class Flight(BaseModel):
    """A single scheduled flight.

    `departureTime` / `arrivalTime` are stored exactly as they appear in the
    dataset: naive ISO-8601 strings in the *local time of their airport*. The
    repository is responsible for attaching the correct timezone when it needs
    real (absolute) instants for duration math.
    """

    flightNumber: str
    airline: str
    origin: str
    destination: str
    departureTime: str
    arrivalTime: str
    price: float
    aircraft: str


# --- API response models -------------------------------------------------


class FlightSegment(BaseModel):
    """One flight leg within an itinerary, as returned to the client."""

    flightNumber: str
    airline: str
    origin: str
    destination: str
    departureTime: str  # local ISO time at origin airport
    arrivalTime: str  # local ISO time at destination airport
    durationMinutes: int
    price: float


class Layover(BaseModel):
    """A connection stop between two consecutive segments."""

    airport: str
    durationMinutes: int


class Itinerary(BaseModel):
    """A complete origin->destination journey (direct or with connections)."""

    segments: list[FlightSegment]
    layovers: list[Layover]
    stops: int = Field(..., description="Number of connection stops (0, 1, or 2)")
    totalDurationMinutes: int
    totalPrice: float


class SearchResponse(BaseModel):
    """Top-level payload for a search request."""

    origin: str
    destination: str
    date: str
    itineraries: list[Itinerary]
