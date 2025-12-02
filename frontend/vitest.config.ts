import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import path from "path";
import { playwright } from "@vitest/browser-playwright";

export default defineConfig({
  plugins: [TanStackRouterVite(), react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "@tanstack/react-query",
      "@tanstack/react-router",
      "@tanstack/router-devtools",
      "zustand",
      "axios",
    ],
  },
  test: {
    // Browser mode configuration
    browser: {
      enabled: true,
      provider: playwright(),
      headless: false, // Set to false for debugging, true for CI
      instances: [
        {
          browser: "chromium",
        },
      ],
      // Configure the base URL for the app
      // Make sure the dev server is running on this port
      ui: false,
    },
    // Setup files
    setupFiles: ["./e2e/setup.ts"],
    // Glob patterns for test files
    include: ["e2e/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}"],
    // Coverage configuration
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: [
        "node_modules/",
        "e2e/",
        "**/*.d.ts",
        "**/*.config.*",
        "**/dist/**",
      ],
    },
    // Global test timeout
    testTimeout: 30000, // Increased for browser tests
    // Hook timeout
    hookTimeout: 30000,
  },
  // Server configuration for browser tests
  server: {
    port: 5173,
  },
});
