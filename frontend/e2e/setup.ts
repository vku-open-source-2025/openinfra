import { beforeAll, afterAll } from "vitest";

// Global test setup for browser e2e tests
// Note: Make sure the dev server is running (npm run dev) before running e2e tests
// The app should be running at http://localhost:5173 (default Vite dev server)

// Track if app has been initialized
let appInitialized = false;

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

    // Wait for document to be ready
    await new Promise((resolve) => {
        if (document.readyState === "complete") {
            resolve(undefined);
        } else {
            window.addEventListener("load", () => resolve(undefined));
        }
    });

    // Check if app is already rendered
    const rootElement = document.getElementById("root");
    if (rootElement && rootElement.children.length > 0) {
        appInitialized = true;
        return;
    }

    // Initialize the app by importing main.tsx
    // This will execute the ReactDOM.render call
    try {
        // Use dynamic import to load the app
        // Note: We need to import it as a side effect, not as a module
        await import("../src/main.tsx");

        // Wait for React to render
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
    } catch (error) {
        console.warn("Failed to initialize app in setup:", error);
        // Continue anyway - tests might still work
    }
});

afterAll(() => {
    // Cleanup code that runs after all tests
    appInitialized = false;
});
