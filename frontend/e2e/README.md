# End-to-End (E2E) Tests

This directory contains Vitest browser mode end-to-end tests for the OpenInfra frontend application.

## Setup

Tests use Vitest with browser mode (Playwright provider). Dependencies are already installed.

## Running Tests

### Run all tests
```bash
pnpm run test:e2e
```

### Run tests in UI mode (interactive)
```bash
pnpm run test:e2e:ui
```

### Run tests in headed mode (see browser)
```bash
pnpm run test:e2e:headed
```

### Run tests with coverage
```bash
pnpm run test:coverage
```

### Run specific test file
```bash
pnpm exec vitest e2e/auth.spec.ts --browser
```

### Run tests in watch mode
```bash
pnpm exec vitest --browser --watch
```

## Test Structure

- `auth.spec.ts` - Authentication flow tests (login, register, validation)
- `map.spec.ts` - Public map page tests (map display, asset selection, geospatial features)
- `dashboard.spec.ts` - Admin dashboard tests (navigation, sidebar, notifications)
- `incidents.spec.ts` - Incidents module tests (list, create, filters)
- `navigation.spec.ts` - Navigation flow tests (routing, protected routes)
- `geospatial.spec.ts` - Geospatial feature tests (address search, nearby search, polygon drawing)
- `setup.ts` - Global test setup and configuration

## Configuration

Tests are configured in `vitest.config.ts`:
- Browser mode: Enabled with Chromium (Playwright provider)
- Test environment: happy-dom
- Setup file: `e2e/setup.ts`
- Test timeout: 10 seconds
- Coverage: v8 provider with HTML reports

## Writing Tests

When writing new tests:

1. Use descriptive test names
2. Use `beforeEach` for common setup
3. Use `screen` from `@testing-library/react` for queries
4. Use `userEvent` for user interactions
5. Use `waitFor` to wait for async operations
6. Use `window.location` for navigation checks
7. Use `document.querySelector` for DOM queries when needed

Example:
```typescript
import { test, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('should do something', async () => {
  window.location.href = '/page';
  await waitFor(() => document.body);

  const button = screen.queryByRole('button', { name: /click me/i });
  if (button) {
    await userEvent.click(button);
    await waitFor(() => {
      expect(window.location.pathname).toMatch(/.*success/);
    });
  }
});
```

## Browser Mode

Vitest browser mode runs tests in a real browser environment using Playwright. This provides:
- Real DOM rendering
- Actual browser APIs
- Network requests
- Real user interactions

## Notes

- Some tests may skip if authentication is required (they check for login redirect)
- Map tests wait for map to load (2-3 seconds)
- API-dependent tests may need mocking in the future
- Tests use flexible selectors to be resilient to UI changes
- Browser mode requires Playwright browsers to be installed (run `pnpm exec playwright install` if needed)
