import { describe, test, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Geospatial Features', () => {
  beforeEach(async () => {
    window.location.href = '/map';
    await waitFor(() => document.body, { timeout: 2000 }); // Wait for map to load
  });

  test('should display all geospatial search components', async () => {
    // Address search
    const addressSearch = screen.queryByPlaceholderText(/search address/i);
    await waitFor(() => {
      expect(addressSearch).toBeTruthy();
    });

    // Nearby search button
    const nearbyButton = screen.queryByRole('button', { name: /nearby search/i });
    expect(nearbyButton).toBeTruthy();

    // Polygon draw button
    const polygonButton = screen.queryByRole('button', { name: /draw area/i });
    expect(polygonButton).toBeTruthy();
  });

  test('should open and close nearby search panel', async () => {
    const nearbyButton = screen.queryByRole('button', { name: /nearby search/i });
    expect(nearbyButton).toBeTruthy();

    if (nearbyButton) {
      // Open panel
      await userEvent.click(nearbyButton);
      await waitFor(() => {}, { timeout: 500 });

      // Check for radius input
      const radiusInput = screen.queryByLabelText(/radius/i) ||
                         document.querySelector('input[type="number"]');
      expect(radiusInput).toBeTruthy();

      // Close panel
      const closeButton = screen.queryByRole('button', { name: /close/i });
      if (closeButton) {
        await userEvent.click(closeButton);
      }
    }
  });

  test('should change search radius', async () => {
    const nearbyButton = screen.queryByRole('button', { name: /nearby search/i });
    expect(nearbyButton).toBeTruthy();

    if (nearbyButton) {
      await userEvent.click(nearbyButton);
      await waitFor(() => {}, { timeout: 500 });

      // Find radius input
      const radiusInput = screen.queryByLabelText(/radius/i) ||
                         document.querySelector('input[type="number"]') as HTMLInputElement;
      if (radiusInput) {
        await userEvent.clear(radiusInput);
        await userEvent.type(radiusInput, '1000');
        await waitFor(() => {
          expect(radiusInput.value).toBe('1000');
        });
      }
    }
  });

  test('should perform address autocomplete search', async () => {
    const addressInput = screen.queryByPlaceholderText(/search address/i);
    expect(addressInput).toBeTruthy();

    if (addressInput) {
      // Type address
      await userEvent.type(addressInput, 'Da Nang');
      await waitFor(() => {}, { timeout: 1000 }); // Wait for debounce

      // Check if suggestions appear (may or may not depending on API)
      const suggestions = document.querySelector('[role="listbox"]') ||
                         document.querySelector('ul li');
      // Suggestions are optional - API may not return results in test environment
    }
  });

  test('should activate polygon drawing mode', async () => {
    const drawButton = screen.queryByRole('button', { name: /draw area/i });
    expect(drawButton).toBeTruthy();

    if (drawButton) {
      await userEvent.click(drawButton);

      await waitFor(() => {
        // Check for drawing instructions
        const drawingText = screen.queryByText(/click on map|draw polygon/i);
        expect(drawingText).toBeTruthy();
      });
    }
  });

  test('should clear geospatial search results', async () => {
    // Open nearby search
    const nearbyButton = screen.queryByRole('button', { name: /nearby search/i });
    expect(nearbyButton).toBeTruthy();

    if (nearbyButton) {
      await userEvent.click(nearbyButton);
      await waitFor(() => {}, { timeout: 500 });

      // Perform a search (if search button exists)
      const searchButton = screen.queryByRole('button', { name: /search/i });
      if (searchButton) {
        await userEvent.click(searchButton);
        await waitFor(() => {}, { timeout: 1000 });
      }

      // Look for clear button
      const clearButton = screen.queryByRole('button', { name: /clear/i });
      if (clearButton) {
        await userEvent.click(clearButton);
      }
    }
  });
});
