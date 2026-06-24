"""Shared fixtures for the backend test suite.

`client` boots the FastAPI app (which loads the dataset on startup) behind a
TestClient. `airports` reads the dataset independently of the application code,
so the tests can verify connection rules (e.g. domestic vs international) without
relying on the same logic they're checking.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def airports() -> dict[str, dict]:
    """Map of airport code -> raw airport record, read straight from the file."""
    with open(config.DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return {a["code"]: a for a in data["airports"]}
