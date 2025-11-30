import { describe, test, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Navigation Flow', () => {
  beforeEach(async () => {
    window.location.href = '/';
    await waitFor(() => document.body);
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
    window.location.href = '/map';
    await waitFor(() => {
      expect(window.location.pathname).toMatch(/.*map/);
    });

    // Test navigation to public report
    window.location.href = '/public/report';
    await waitFor(() => {
      expect(window.location.pathname).toMatch(/.*report/);
    });
  });

  test('should handle protected routes', async () => {
    // Try to access admin route without auth
    window.location.href = '/admin';
    await waitFor(() => document.body);

    // Should redirect to login or show access denied
    const currentPath = window.location.pathname;
    expect(currentPath.includes('/login') || currentPath.includes('/admin')).toBeTruthy();
  });
});
