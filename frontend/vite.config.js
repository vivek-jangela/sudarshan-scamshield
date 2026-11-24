import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Dev: npm run dev (port 5173) proxies /api to the FastAPI backend on :8000.
// Prod: npm run build, then copy dist/* into backend/static/ (FastAPI serves it at http://localhost:8000/).
export default defineConfig({
  plugins: [react()],
  base: "/",
  server: { proxy: { "/api": "http://localhost:8000" } },
});
