import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Single-bundle app (React + react-select + Leaflet) sits just over 500 kB
  // minified; raise the advisory limit so build output stays clean.
  build: {
    chunkSizeWarningLimit: 600,
  },
});
