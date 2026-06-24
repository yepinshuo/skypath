"""SkyPath backend — FastAPI application.

Wires together the dataset (loaded once on startup), the search layer, and the
HTTP API the frontend talks to. The `/search` endpoint validates and normalizes
its inputs, runs the connection search, and returns itineraries sorted by total
travel time.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date as Date
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .data import repository
from .models import SearchResponse
from .search import search_itineraries

logger = logging.getLogger("skypath")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the dataset once when the service starts."""
    repository.load(config.DATA_FILE)
    logger.info(
        "Loaded dataset: %d airports, %d flights (%d skipped)",
        repository.airport_count,
        repository.flight_count,
        repository.skipped_count,
    )
    yield


app = FastAPI(title="SkyPath", version="0.1.0", lifespan=lifespan)

# Allow the frontend dev/container origin to call the API. Tightened later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --- Request validation helpers ------------------------------------------


def _parse_airport_code(value: str, field: str) -> str:
    """Normalize and validate a 3-letter IATA code (case-insensitive input)."""
    code = value.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise HTTPException(
            status_code=400,
            detail=f"{field} must be a 3-letter IATA airport code (e.g. JFK)",
        )
    return code


def _parse_date(value: str) -> Date:
    """Validate an ISO 8601 calendar date (YYYY-MM-DD)."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="date must be in ISO 8601 format YYYY-MM-DD",
        )


# --- Endpoints -----------------------------------------------------------


@app.get("/health")
def health() -> dict:
    """Liveness + dataset sanity check."""
    return {
        "status": "ok",
        "airports": repository.airport_count,
        "flights": repository.flight_count,
    }


@app.get("/search", response_model=SearchResponse)
def search(origin: str, destination: str, date: str) -> SearchResponse:
    """Search valid itineraries between two airports on a date.

    Validation:
      * `origin`/`destination` must be 3-letter IATA codes (normalized to upper)
      * `date` must be ISO 8601 (YYYY-MM-DD)
      * origin and destination must differ
      * both airports must exist in the dataset

    Malformed input and same origin/destination return 400; an unknown airport
    code returns 404. A valid route with no available itineraries returns 200
    with an empty list (the frontend renders this as an empty state).
    """
    origin_code = _parse_airport_code(origin, "origin")
    destination_code = _parse_airport_code(destination, "destination")
    day = _parse_date(date)

    if origin_code == destination_code:
        raise HTTPException(
            status_code=400, detail="origin and destination must be different"
        )

    for code in (origin_code, destination_code):
        if repository.get_airport(code) is None:
            raise HTTPException(status_code=404, detail=f"unknown airport code: {code}")

    itineraries = search_itineraries(repository, origin_code, destination_code, day)
    return SearchResponse(
        origin=origin_code,
        destination=destination_code,
        date=day.isoformat(),
        itineraries=itineraries,
    )
