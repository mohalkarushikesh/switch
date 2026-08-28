import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During `npm run dev`, proxy API calls to the FastAPI backend on :8000 so the
// browser can use same-origin relative URLs (no CORS). `npm run build` emits a
// static bundle into dist/ that FastAPI serves at /app.
const API = 'http://localhost:8000'
const proxy = Object.fromEntries(
  ['/invoices', '/health', '/stats', '/metrics', '/ledger', '/policies', '/audit'].map(
    (p) => [p, { target: API, changeOrigin: true }],
  ),
)

export default defineConfig({
  plugins: [react()],
  base: '/app/',
  build: { outDir: 'dist' },
  server: { port: 5173, proxy },
})
