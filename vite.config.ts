import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  // Serve from project root so Vite uses root index.html which imports /src/main.ts
  root: '.',
  server: {
    port: 5173,
    open: true
  },
  build: {
    outDir: path.resolve(__dirname, 'dist'),
    emptyOutDir: true
  },
  resolve: {
    alias: {
      '@sim': path.resolve(__dirname, 'game_sim_ts')
    }
  }
});


