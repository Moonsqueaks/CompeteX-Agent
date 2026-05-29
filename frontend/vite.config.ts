import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  cacheDir: ".vite-cache",
  plugins: [react()],
  root: frontendRoot,
  test: {
    environment: "jsdom",
    exclude: ["e2e/**", "node_modules/**", "dist/**"],
    maxWorkers: 1,
    pool: "vmThreads"
  }
});
