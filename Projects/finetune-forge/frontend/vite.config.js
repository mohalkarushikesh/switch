import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev we proxy /api to the FastAPI backend so the browser makes same-origin
// requests (no CORS) and the frontend code stays deployment-agnostic.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
