import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: Number(process.env.VITE_DEV_PORT) || 5173,
    host: process.env.VITE_DEV_HOST || '0.0.0.0',
  },
  build: {
    outDir: process.env.BUILD_OUT ?? 'dist',
  },
});
