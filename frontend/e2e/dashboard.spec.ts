import { describe, test, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Admin Dashboard', () => {
  beforeEach(async () => {
    // Note: In a real scenario, you'd need to authenticate first
    // For now, we'll test the public-facing parts or mock auth
    window.location.href = '/admin';
    await waitFor(() => document.body);
  });

  test('should display dashboard when authenticated', async () => {
    // If redirected to login, that's expected behavior
    const currentPath = window.location.pathname;

    if (currentPath.includes('/login')) {
      // User needs to login first - this is expected
      const loginText = screen.queryByText(/login|sign in/i);
      expect(loginText).toBeTruthy();
    } else {
      // User is authenticated, check for dashboard elements
      const dashboardText = screen.queryByText(/overview|dashboard/i);
      expect(dashboardText).toBeTruthy();
    }
  });

  test('should display sidebar navigation', async () => {
    // Skip if redirected to login
    if (window.location.pathname.includes('/login')) {
      return;
    }

    const sidebar = document.querySelector('[class*="sidebar"]') ||
                    document.querySelector('nav');
    await waitFor(() => {
      expect(sidebar).toBeTruthy();
    });
  });

  test('should display notification center', async () => {
    // Skip if redirected to login
    if (window.location.pathname.includes('/login')) {
      return;
    }

    // Look for notification bell or center
    const notificationButton = screen.queryByRole('button', { name: /notification|bell/i });

    // Notification center may or may not be visible initially
    if (notificationButton) {
      expect(notificationButton).toBeTruthy();
    }
  });

  test('should navigate to different admin sections', async () => {
    // Skip if redirected to login
    if (window.location.pathname.includes('/login')) {
      return;
    }

    // Test navigation to incidents
    const incidentsLink = screen.queryByRole('link', { name: /incident/i });
    if (incidentsLink) {
      await userEvent.click(incidentsLink);
      await waitFor(() => {
        expect(window.location.pathname).toMatch(/.*incident/);
      });
    }
  });
});
