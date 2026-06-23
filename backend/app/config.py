"""Application configuration and connection-rule constants.

Connection rules are defined by the SkyPath spec and kept here as named
constants so the search logic reads declaratively and the rules are easy to
audit / tune in one place.
"""

import os

# --- Connection rules (from the spec) ------------------------------------

# Minimum time a passenger needs between an arriving and a departing flight.
MIN_LAYOVER_DOMESTIC_MINUTES = 45
MIN_LAYOVER_INTERNATIONAL_MINUTES = 90

# A layover longer than this is not considered a valid connection.
MAX_LAYOVER_MINUTES = 6 * 60  # 6 hours

# Maximum number of connection stops (2-stop connection => 3 flight segments).
MAX_STOPS = 2

# --- Runtime settings ----------------------------------------------------

# Path to the flight dataset. Overridable via env var for Docker / tests.
DATA_FILE = os.getenv(
    "SKYPATH_DATA_FILE",
    os.path.join(os.path.dirname(__file__), "..", "..", "flights.json"),
)
