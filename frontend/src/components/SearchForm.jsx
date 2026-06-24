// Search form: origin, destination, date. Validates on submit and surfaces
// clear, field-level messages before a request is ever sent.

import { useState } from "react";

const CODE_RE = /^[A-Za-z]{3}$/;

// Sensible defaults so the tool returns results on first use — the dataset
// only covers 2024-03-15.
const DEFAULTS = { origin: "JFK", destination: "LAX", date: "2024-03-15" };

export default function SearchForm({ onSearch, loading }) {
  const [values, setValues] = useState(DEFAULTS);
  const [errors, setErrors] = useState({});

  const set = (key) => (e) => {
    const raw = e.target.value;
    const value = key === "date" ? raw : raw.toUpperCase();
    setValues((v) => ({ ...v, [key]: value }));
  };

  function validate(v) {
    const next = {};
    if (!CODE_RE.test(v.origin.trim())) next.origin = "Enter a 3-letter airport code.";
    if (!CODE_RE.test(v.destination.trim()))
      next.destination = "Enter a 3-letter airport code.";
    if (!next.origin && !next.destination && v.origin.trim() === v.destination.trim())
      next.destination = "Origin and destination must be different.";
    if (!v.date) next.date = "Pick a date.";
    return next;
  }

  function submit() {
    const next = validate(values);
    setErrors(next);
    if (Object.keys(next).length === 0) {
      onSearch({
        origin: values.origin.trim(),
        destination: values.destination.trim(),
        date: values.date,
      });
    }
  }

  const onKeyDown = (e) => {
    if (e.key === "Enter") submit();
  };

  return (
    <div className="panel">
      <div className="route-row">
        <div className={`field code${errors.origin ? " invalid" : ""}`}>
          <label htmlFor="origin">From</label>
          <input
            id="origin"
            value={values.origin}
            onChange={set("origin")}
            onKeyDown={onKeyDown}
            placeholder="JFK"
            maxLength={3}
            autoComplete="off"
            aria-invalid={!!errors.origin}
          />
        </div>

        <div className="swap" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M4 9h13M13 5l4 4-4 4M20 15H7M11 19l-4-4 4-4"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        <div className={`field code${errors.destination ? " invalid" : ""}`}>
          <label htmlFor="destination">To</label>
          <input
            id="destination"
            value={values.destination}
            onChange={set("destination")}
            onKeyDown={onKeyDown}
            placeholder="LAX"
            maxLength={3}
            autoComplete="off"
            aria-invalid={!!errors.destination}
          />
        </div>
      </div>

      {(errors.origin || errors.destination) && (
        <div className="field-error">{errors.origin || errors.destination}</div>
      )}

      <div className="date-row">
        <div className={`field${errors.date ? " invalid" : ""}`}>
          <label htmlFor="date">Depart</label>
          <input
            id="date"
            type="date"
            value={values.date}
            onChange={set("date")}
            onKeyDown={onKeyDown}
            aria-invalid={!!errors.date}
          />
          {errors.date && <div className="field-error">{errors.date}</div>}
        </div>

        <button className="search-btn" onClick={submit} disabled={loading}>
          {loading ? "Searching…" : "Search flights"}
        </button>
      </div>
    </div>
  );
}
