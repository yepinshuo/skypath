"""SkyPath backend — FastAPI application.

Wires together the dataset (loaded once on startup), the search layer, and the
HTTP API the frontend talks to. In the skeleton the search endpoint is present
but returns 501 Not Implemented; request parsing/validation and the call into
the search layer are completed in later commits.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config
from .data import repository

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


@app.get("/health")
def health() -> dict:
    """Liveness + dataset sanity check."""
    return {
        "status": "ok",
        "airports": repository.airport_count,
        "flights": repository.flight_count,
    }


@app.get("/search")
def search(origin: str, destination: str, date: str) -> JSONResponse:
    """Search valid itineraries between two airports on a date.

    TODO (step 4): validate inputs (IATA codes, ISO date, origin != dest),
    call search_itineraries, and return a SearchResponse sorted by total time.
    """
    return JSONResponse(
        status_code=501,
        content={"detail": "search not implemented yet (skeleton)"},
    )
