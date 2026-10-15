import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": new URL("./src", import.meta.url).pathname } },
  test: {
    environment: "node",
    include: ["src/**/*.test.{ts,tsx}"],
    fileParallelism: false, // database suites share one test database
    env: loadEnv("test", process.cwd(), ""),
  },
});
