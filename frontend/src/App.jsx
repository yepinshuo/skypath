// App shell. Owns the search lifecycle (idle → loading → done/error) and hands
// the right slice of state to the form and the results area.

import { useState } from "react";
import SearchForm from "./components/SearchForm.jsx";
import Results from "./components/Results.jsx";
import { searchItineraries } from "./api.js";

export default function App() {
  const [status, setStatus] = useState("idle");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState(null);

  async function handleSearch(values) {
    setQuery(values);
    setStatus("loading");
    setError(null);
    try {
      const result = await searchItineraries(values);
      setData(result);
      setStatus("done");
    } catch (e) {
      setError(e.message);
      setStatus("error");
    }
  }

  return (
    <div className="page">
      <header className="masthead">
        <span className="wordmark">
          SkyPath<span className="dot">.</span>
        </span>
        <span className="tagline">Find your way there — direct or connecting.</span>
      </header>

      <SearchForm onSearch={handleSearch} loading={status === "loading"} />
      <Results status={status} data={data} error={error} query={query} />
    </div>
  );
}
