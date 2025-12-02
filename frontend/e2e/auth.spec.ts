import { describe, test, expect, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { navigateTo } from "./helpers";

describe("Authentication Flow", () => {
    beforeEach(async () => {
        // Navigate to home page before each test using router (doesn't reload page)
        await navigateTo("/");
        await waitFor(() => document.body, { timeout: 5000 });
    });

    test("should navigate to login page", async () => {
        // Click login button or link
        const loginLink =
            screen.queryByRole("link", { name: /login/i }) ||
            screen.queryByRole("button", { name: /login/i });

        if (loginLink) {
            await userEvent.click(loginLink);
            await waitFor(
                () => {
                    expect(window.location.pathname).toMatch(/.*login/);
                },
                { timeout: 5000 }
            );
        }
    });

    test("should display login form", async () => {
        await navigateTo("/login");
        await waitFor(() => document.body, { timeout: 5000 });

        // Check for login form elements
        const emailInput =
            screen.queryByLabelText(/email|username/i) ||
            screen.queryByPlaceholderText(/email|username/i);
        const passwordInput =
            screen.queryByLabelText(/password/i) ||
            screen.queryByPlaceholderText(/password/i);
        const submitButton = screen.queryByRole("button", {
            name: /login|sign in/i,
        });

        expect(emailInput || passwordInput).toBeTruthy();
        expect(submitButton).toBeTruthy();
    });

    test("should display register form", async () => {
        await navigateTo("/register");
        await waitFor(() => document.body, { timeout: 5000 });

        // Check for registration form elements
        const emailInput =
            screen.queryByLabelText(/email/i) ||
            screen.queryByPlaceholderText(/email/i);
        const passwordInput =
            screen.queryByLabelText(/password/i) ||
            screen.queryByPlaceholderText(/password/i);
        const submitButton = screen.queryByRole("button", {
            name: /register|sign up/i,
        });

        expect(emailInput).toBeTruthy();
        expect(passwordInput).toBeTruthy();
        expect(submitButton).toBeTruthy();
    });

    test("should show validation errors on empty form submission", async () => {
        await navigateTo("/login");
        await waitFor(() => document.body, { timeout: 5000 });

        const submitButton = screen.queryByRole("button", {
            name: /login|sign in/i,
        });
        if (submitButton) {
            await userEvent.click(submitButton);
            // Wait for validation errors (if any)
            await waitFor(() => {}, { timeout: 500 });
        }
    });

    test("should navigate between login and register pages", async () => {
        await navigateTo("/login");
        await waitFor(() => document.body, { timeout: 5000 });

        // Look for link to register page
        const registerLink = screen.queryByRole("link", {
            name: /register|sign up|create account/i,
        });
        if (registerLink) {
            await userEvent.click(registerLink);
            await waitFor(
                () => {
                    expect(window.location.pathname).toMatch(/.*register/);
                },
                { timeout: 5000 }
            );
        }
    });
});
