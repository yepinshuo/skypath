import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The frontend reads the backend base URL from VITE_API_BASE_URL
// (set in docker-compose) and falls back to localhost for local dev.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
