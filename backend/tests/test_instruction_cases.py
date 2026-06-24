"""The six test cases from the SkyPath instructions.

Each test maps to one row of the instructions' "Test Cases" table and asserts
the documented expected behavior. These are exercised through the HTTP endpoint
so they cover request validation and the response shape as well as the search.
"""

DATE = "2024-03-15"


def _search(client, origin, destination, date=DATE):
    return client.get(
        "/search",
        params={"origin": origin, "destination": destination, "date": date},
    )


def _is_domestic_connection(airports, arriving, departing):
    """A connection is domestic iff both flights stay within one country."""
    return (
        airports[arriving["origin"]]["country"]
        == airports[arriving["destination"]]["country"]
        == airports[departing["destination"]]["country"]
    )


# Case 1 — JFK -> LAX: returns direct flights AND multi-stop options,
# sorted by total travel time.
def test_case1_direct_and_multistop(client):
    res = _search(client, "JFK", "LAX")
    assert res.status_code == 200
    itineraries = res.json()["itineraries"]

    assert itineraries, "expected itineraries for JFK -> LAX"
    assert any(it["stops"] == 0 for it in itineraries), "expected at least one direct flight"
    assert any(it["stops"] >= 1 for it in itineraries), "expected multi-stop options"

    durations = [it["totalDurationMinutes"] for it in itineraries]
    assert durations == sorted(durations), "results must be sorted by total travel time"


# Case 2 — SFO -> NRT: international route, 90-minute minimum layover applies.
def test_case2_international_layover(client, airports):
    res = _search(client, "SFO", "NRT")
    assert res.status_code == 200
    itineraries = res.json()["itineraries"]
    assert itineraries, "expected itineraries for SFO -> NRT"

    saw_international = False
    for it in itineraries:
        segments = it["segments"]
        for index, layover in enumerate(it["layovers"]):
            arriving, departing = segments[index], segments[index + 1]
            domestic = _is_domestic_connection(airports, arriving, departing)
            minimum = 45 if domestic else 90
            if not domestic:
                saw_international = True
            assert layover["durationMinutes"] >= minimum, (
                f"{'domestic' if domestic else 'international'} layover "
                f"{layover['durationMinutes']}m below minimum {minimum}m"
            )
            assert layover["durationMinutes"] <= 360, "layover exceeds 6-hour maximum"

    assert saw_international, "SFO -> NRT should include an international connection"


# Case 3 — BOS -> SEA: no direct flight exists, must find connections.
def test_case3_requires_connection(client):
    res = _search(client, "BOS", "SEA")
    assert res.status_code == 200
    itineraries = res.json()["itineraries"]

    assert itineraries, "expected connecting itineraries for BOS -> SEA"
    assert all(it["stops"] >= 1 for it in itineraries), "no direct BOS -> SEA flight should exist"


# Case 4 — JFK -> JFK: empty results or validation error.
def test_case4_same_origin_and_destination(client):
    res = _search(client, "JFK", "JFK")
    if res.status_code == 200:
        assert res.json()["itineraries"] == [], "same-airport search should yield no itineraries"
    else:
        assert res.status_code == 400, "same-airport search should be a 400 validation error"


# Case 5 — XXX -> LAX: invalid airport code, graceful error handling.
def test_case5_invalid_airport_code(client):
    res = _search(client, "XXX", "LAX")
    assert res.status_code == 404, "unknown airport code should return a 404, not a 500"
    assert "XXX" in res.json()["detail"], "error should name the offending code"


# Case 6 — SYD -> LAX: date-line crossing; arrival appears "before" departure in
# local time, yet the real (timezone-aware) duration is positive.
def test_case6_date_line_crossing(client):
    res = _search(client, "SYD", "LAX")
    assert res.status_code == 200
    itineraries = res.json()["itineraries"]

    directs = [it for it in itineraries if it["stops"] == 0]
    assert directs, "expected a direct SYD -> LAX flight"

    def local_clock(iso):
        return iso[11:16]

    appears_reversed = any(
        local_clock(it["segments"][0]["arrivalTime"])
        < local_clock(it["segments"][0]["departureTime"])
        for it in directs
    )
    assert appears_reversed, "expected arrival to appear earlier than departure in local time"
    assert all(it["totalDurationMinutes"] > 0 for it in directs), "real duration must be positive"
