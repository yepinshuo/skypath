// Results area: owns the loading / error / empty / results states. Each state
// gives the traveler direction rather than just a status word.

import Itinerary from "./Itinerary.jsx";

export default function Results({ status, data, error, query }) {
  if (status === "idle") return null;

  if (status === "loading") {
    return (
      <div className="results">
        <div className="skeleton" />
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="results">
        <div className="notice error">
          <div className="title">Search failed</div>
          <div className="body">{error}</div>
        </div>
      </div>
    );
  }

  // status === "done"
  const itineraries = data?.itineraries ?? [];

  if (itineraries.length === 0) {
    return (
      <div className="results">
        <div className="notice">
          <div className="title">No itineraries found</div>
          <div className="body">
            No flights connect {query.origin} → {query.destination} on {query.date} within
            two stops. Try a different date or route.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="results">
      <div className="results-head">
        <span className="route">
          {data.origin} → {data.destination}
        </span>
        <span className="count">
          {itineraries.length} {itineraries.length === 1 ? "option" : "options"} · by total
          time
        </span>
      </div>
      {itineraries.map((it, i) => (
        <Itinerary key={i} itinerary={it} />
      ))}
    </div>
  );
}
