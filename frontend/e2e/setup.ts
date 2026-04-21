import { beforeAll, afterAll } from "vitest";
import "../src/main.tsx";

// Global test setup for browser e2e tests
// Note: Make sure the dev server is running (npm run dev) before running e2e tests
// The app should be running at http://localhost:5173 (default Vite dev server)

// Track if app has been initialized
let appInitialized = false;

async function waitForDocumentReady(timeoutMs = 2000) {
    if (typeof document === "undefined") {
        return;
    }

    // In Vitest browser mode, `load` may never fire for the test iframe.
    // Treat anything beyond `loading` as ready and fallback on a short timeout.
    if (document.readyState !== "loading") {
        return;
    }

    await Promise.race([
        new Promise<void>((resolve) => {
            document.addEventListener("DOMContentLoaded", () => resolve(), {
                once: true,
            });
        }),
        new Promise<void>((resolve) => {
            window.addEventListener("load", () => resolve(), { once: true });
        }),
        new Promise<void>((resolve) => {
            window.setTimeout(() => resolve(), timeoutMs);
        }),
    ]);
}

beforeAll(async () => {
    // Initialize the React app in browser tests
    if (typeof window === "undefined" || appInitialized) {
        return;
    }

    // Ensure root element exists
    if (!document.getElementById("root")) {
        const root = document.createElement("div");
        root.id = "root";
        document.body.appendChild(root);
    }

    // Wait briefly for the document lifecycle to settle.
    await waitForDocumentReady();

    // Check if app is already rendered
    const rootElement = document.getElementById("root");
    if (rootElement && rootElement.children.length > 0) {
        appInitialized = true;
        return;
    }

    // Wait for React to render after static app bootstrap import.
    let attempts = 0;
    while (attempts < 50) {
        const root = document.getElementById("root");
        if (root && root.children.length > 0) {
            appInitialized = true;
            // Wait a bit more for router to initialize
            await new Promise((resolve) => setTimeout(resolve, 500));
            return;
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
        attempts++;
    }

    throw new Error("Failed to initialize app in setup: root did not render in time.");
});

afterAll(() => {
    // Cleanup code that runs after all tests
    appInitialized = false;
});
