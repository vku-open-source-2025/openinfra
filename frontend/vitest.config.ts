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
    test: {
        // Browser mode configuration
        browser: {
            enabled: true,
            name: "chromium",
            provider: playwright(),
            headless: true,
            instances: ["chromium"],
        },
        // Test environment - not needed for browser mode, browser provides the environment
        // environment: 'happy-dom', // Commented out for browser mode
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
        testTimeout: 10000,
        // Hook timeout
        hookTimeout: 10000,
    },
});
