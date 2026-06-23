// App shell. Composes the search form and results view, and will own the
// search state (query, loading, results, error) once wired up in step 5.

import SearchForm from "./components/SearchForm.jsx";
import Results from "./components/Results.jsx";

export default function App() {
  return (
    <main>
      <h1>SkyPath</h1>
      <SearchForm />
      <Results />
    </main>
  );
}
