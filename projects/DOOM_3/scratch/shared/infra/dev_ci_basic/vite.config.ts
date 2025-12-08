import { defineConfig } from 'vite'

// Simple Vite config for a minimal dev server
export default defineConfig({
  server: {
    host: true,
    port: 5173,
  },
  build: {
    sourcemap: true,
    outDir: 'dist',
  }
})
