import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));
const reactRouterDomEsm = fileURLToPath(
  new URL("./node_modules/react-router-dom/dist/index.mjs", import.meta.url)
);
const reactRouterDomSubpathEsm = fileURLToPath(
  new URL("./node_modules/react-router/dist/development/dom-export.mjs", import.meta.url)
);

export default defineConfig({
  cacheDir: process.env.VITE_CACHE_DIR ?? ".vite-cache",
  plugins: [react()],
  resolve: {
    alias: {
      "react-router-dom": reactRouterDomEsm,
      "react-router/dom": reactRouterDomSubpathEsm
    }
  },
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
    fileParallelism: false,
    maxWorkers: 1,
    pool: "forks",
    setupFiles: ["src/test/setup.ts"],
    testTimeout: 20000,
    deps: {
      web: {
        transformGlobPattern: [/node_modules\/react-router\//, /node_modules\/react-router-dom\//]
      }
    },
    server: {
      deps: {
        inline: ["react-router", "react-router-dom"]
      }
    }
  }
});
