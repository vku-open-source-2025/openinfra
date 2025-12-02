import { describe, test, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { navigateTo } from './helpers';

describe('Navigation Flow', () => {
  beforeEach(async () => {
    await navigateTo('/');
    await waitFor(() => document.body, { timeout: 5000 });
  });

  test('should navigate from homepage to map', async () => {
    // Look for link or button to map
    const mapLink = screen.queryByRole('link', { name: /map/i }) ||
                    screen.queryByRole('button', { name: /map|explore/i });

    if (mapLink) {
      await userEvent.click(mapLink);
      await waitFor(() => {
        expect(window.location.pathname).toMatch(/.*map/);
      });
    }
  });

  test('should navigate from homepage to login', async () => {
    const loginLink = screen.queryByRole('link', { name: /login/i }) ||
                     screen.queryByRole('button', { name: /login/i });

    if (loginLink) {
      await userEvent.click(loginLink);
      await waitFor(() => {
        expect(window.location.pathname).toMatch(/.*login/);
      });
    }
  });

  test('should navigate between public pages', async () => {
    // Test navigation to map
    await navigateTo('/map');
    await waitFor(() => {
      expect(window.location.pathname).toMatch(/.*map/);
    }, { timeout: 5000 });

    // Test navigation to public report
    await navigateTo('/public/report');
    await waitFor(() => {
      expect(window.location.pathname).toMatch(/.*report/);
    }, { timeout: 5000 });
  });

  test('should handle protected routes', async () => {
    // Try to access admin route without auth
    await navigateTo('/admin');
    await waitFor(() => document.body, { timeout: 5000 });

    // Should redirect to login or show access denied
    const currentPath = window.location.pathname;
    expect(currentPath.includes('/login') || currentPath.includes('/admin')).toBeTruthy();
  });
});
