import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Component tests run in jsdom; `globals: true` exposes describe/it/expect.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
