import { defineConfig } from "vite";

// In development the viewer runs on Vite and talks to the Python server on :8000.
export default defineConfig({
  server: { proxy: { "/stream": { target: "ws://127.0.0.1:8000", ws: true } } },
});
