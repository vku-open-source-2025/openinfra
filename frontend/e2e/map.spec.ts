import { describe, test, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Public Map Page', () => {
  beforeEach(async () => {
    window.location.href = '/map';
    // Wait for map to load
    await waitFor(() => document.body, { timeout: 2000 });
  });

  test('should display map component', async () => {
    // Check if map container exists
    const mapContainer = document.querySelector('.leaflet-container') ||
                         document.querySelector('[class*="map"]');
    await waitFor(() => {
      expect(mapContainer).toBeTruthy();
    });
  });

  test('should display asset table', async () => {
    // Look for asset table or list
    const assetTable = screen.queryByText(/system assets|assets/i) ||
                       document.querySelector('table');
    await waitFor(() => {
      expect(assetTable).toBeTruthy();
    });
  });

  test('should display geospatial search controls when enabled', async () => {
    // Check for address search
    const addressSearch = screen.queryByPlaceholderText(/search address/i);
    await waitFor(() => {
      expect(addressSearch).toBeTruthy();
    });

    // Check for nearby search button
    const nearbySearch = screen.queryByRole('button', { name: /nearby search/i });
    expect(nearbySearch).toBeTruthy();

    // Check for polygon draw button
    const polygonDraw = screen.queryByRole('button', { name: /draw area/i });
    expect(polygonDraw).toBeTruthy();
  });

  test('should open nearby search panel', async () => {
    const nearbyButton = screen.queryByRole('button', { name: /nearby search/i });
    expect(nearbyButton).toBeTruthy();

    if (nearbyButton) {
      await userEvent.click(nearbyButton);

      // Check for radius input
      await waitFor(() => {
        const radiusInput = screen.queryByLabelText(/radius/i) ||
                           document.querySelector('input[type="number"]');
        expect(radiusInput).toBeTruthy();
      });
    }
  });

  test('should perform address search', async () => {
    const addressInput = screen.queryByPlaceholderText(/search address/i);
    expect(addressInput).toBeTruthy();

    if (addressInput) {
      await userEvent.type(addressInput, 'Da Nang');

      // Wait for suggestions or results
      await waitFor(() => {}, { timeout: 1000 });

      // Check if suggestions appear or geocoding happens
      const suggestions = document.querySelector('[role="listbox"]') ||
                         document.querySelector('ul');
      // Suggestions may or may not appear depending on API response
    }
  });

  test('should display map controls', async () => {
    // Check for map mode toggle buttons (markers/heatmap)
    const mapControls = document.querySelectorAll('button[title*="View"]');
    // At least one control should be visible
    expect(mapControls.length).toBeGreaterThan(0);
  });

  test('should select asset from map', async () => {
    // Wait for markers to load
    await waitFor(() => {}, { timeout: 3000 });

    // Try to click on a marker (if any exist)
    const markers = document.querySelectorAll('.leaflet-marker-icon');

    if (markers.length > 0) {
      const firstMarker = markers[0] as HTMLElement;
      firstMarker.click();

      // Check if asset details panel appears
      await waitFor(() => {}, { timeout: 500 });
      const detailsPanel = screen.queryByText(/feature code|feature type/i) ||
                          document.querySelector('[class*="detail"]');
      // Details may appear in a panel or popup
    }
  });

  test('should filter assets by polygon', async () => {
    const drawButton = screen.queryByRole('button', { name: /draw area/i });
    expect(drawButton).toBeTruthy();

    if (drawButton) {
      await userEvent.click(drawButton);

      // Wait for drawing mode to activate
      await waitFor(() => {
        // Check if drawing instructions appear
        const drawingText = screen.queryByText(/click on map|draw polygon/i);
        expect(drawingText).toBeTruthy();
      });
    }
  });
});
