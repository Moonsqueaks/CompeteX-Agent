import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  cacheDir: process.env.VITE_CACHE_DIR ?? ".vite-cache",
  plugins: [react()],
  root: frontendRoot,
  test: {
    environment: "jsdom",
    exclude: [
      "e2e/**",
      "node_modules/**",
      "dist/**",
      ".playwright-results*/**",
      ".vite-build-check*/**",
      ".vite-cache*/**",
      "playwright-report/**",
      "test-results/**"
    ],
    maxWorkers: 1,
    pool: "vmThreads",
    setupFiles: ["src/test/setup.ts"],
    deps: {
      web: {
        transformGlobPattern: [/node_modules\/react-router\//]
      }
    },
    server: {
      deps: {
        inline: ["react-router", "react-router-dom"]
      }
    }
  }
});
