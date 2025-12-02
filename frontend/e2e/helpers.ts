/**
 * Helper utilities for e2e browser tests
 * These functions work with Vitest browser mode and TanStack Router
 */

/**
 * Navigate to a route using the router (doesn't reload the page)
 * This is safe to use in Vitest browser tests
 *
 * Note: In Vitest browser mode, we need to avoid window.location.href
 * as it causes page reloads. Instead, we use history API and let
 * the router handle the navigation.
 */
export async function navigateTo(path: string) {
    if (typeof window === "undefined") {
        return;
    }

    // Ensure app is loaded (should be done in setup, but double-check)
    const rootElement = document.getElementById("root");
    if (!rootElement || rootElement.children.length === 0) {
        // Wait a bit for app to load
        await new Promise((resolve) => setTimeout(resolve, 500));
    }

    const fullPath = path.startsWith("/") ? path : `/${path}`;

    // Use history API to change URL without reloading
    // TanStack Router listens to popstate events
    window.history.pushState({}, "", fullPath);

    // Dispatch popstate event to trigger router navigation
    const popStateEvent = new PopStateEvent("popstate", {
        state: {},
    });
    window.dispatchEvent(popStateEvent);

    // Also try to trigger hashchange if it's a hash route
    if (fullPath.includes("#")) {
        window.dispatchEvent(new HashChangeEvent("hashchange"));
    }

    // Wait for router to process the navigation
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Wait for the pathname to actually change
    let attempts = 0;
    while (window.location.pathname !== fullPath && attempts < 50) {
        await new Promise((resolve) => setTimeout(resolve, 50));
        attempts++;
    }

    // Wait a bit more for React to render the new route
    await new Promise((resolve) => setTimeout(resolve, 500));
}

/**
 * Get current pathname
 */
export function getCurrentPath(): string {
    return typeof window !== "undefined" ? window.location.pathname : "";
}

/**
 * Wait for an element to appear in the DOM
 */
export async function waitForElement(
    selector: string | (() => HTMLElement | null),
    timeout = 5000
): Promise<HTMLElement> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
        const element =
            typeof selector === "string"
                ? (document.querySelector(selector) as HTMLElement)
                : selector();

        if (element) {
            return element;
        }

        await new Promise((resolve) => setTimeout(resolve, 100));
    }

    throw new Error(`Element not found within ${timeout}ms`);
}
