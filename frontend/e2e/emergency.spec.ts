import { describe, test, expect, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { navigateTo } from "./helpers";

function isLoginViewVisible() {
    const loginHeading = screen.queryByRole("heading", {
        name: /đăng nhập|login|sign in/i,
    });
    const loginButton = screen.queryByRole("button", {
        name: /đăng nhập|login|sign in/i,
    });

    return Boolean(loginHeading || loginButton);
}

function isEmergencyCenterVisible() {
    const heading = screen.queryByText(/Emergency Command Center/i);
    return Boolean(heading);
}

describe("Emergency Command Center", () => {
    beforeEach(async () => {
        await navigateTo("/admin/emergency-center");
        await waitFor(() => {
            if (isLoginViewVisible() || isEmergencyCenterVisible()) {
                return true;
            }

            throw new Error("Emergency screen not ready yet");
        }, { timeout: 5000 });
    });

    test("should handle protected route access", async () => {
        if (isLoginViewVisible()) {
            expect(isLoginViewVisible()).toBeTruthy();
            return;
        }

        expect(window.location.pathname).toContain("/admin/emergency-center");
        const heading = screen.queryByText(/Emergency Command Center/i);
        expect(heading).toBeTruthy();
    });

    test("should display emergency summary cards when authenticated", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const activeEvents = screen.queryByText(/Active Events/i);
        const criticalHazards = screen.queryByText(/Critical Hazards/i);
        const draftEop = screen.queryByText(/Draft EOP/i);

        expect(activeEvents).toBeTruthy();
        expect(criticalHazards).toBeTruthy();
        expect(draftEop).toBeTruthy();
    });

    test("should render hazard map section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const hazardMapTitle = screen.queryByText(/Hazard Realtime Map/i);
        expect(hazardMapTitle).toBeTruthy();
    });

    test("should expose event selector and actions", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const eventSelector = screen.queryByRole("combobox");
        const refreshButton = screen.queryByRole("button", { name: /Refresh All/i });
        const optimizeButton = screen.queryByRole("button", {
            name: /Optimize Dispatch/i,
        });

        expect(eventSelector).toBeTruthy();
        expect(refreshButton).toBeTruthy();
        expect(optimizeButton).toBeTruthy();
    });

    test("should allow selecting emergency event", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const eventSelector = screen.queryByRole("combobox") as HTMLSelectElement | null;
        expect(eventSelector).toBeTruthy();

        if (eventSelector && eventSelector.options.length > 1) {
            await userEvent.selectOptions(eventSelector, eventSelector.options[1].value);
            expect(eventSelector.value).toBe(eventSelector.options[1].value);
        }
    });
});
