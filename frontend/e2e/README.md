# End-to-End (E2E) Tests

This directory contains Vitest browser mode end-to-end tests for the OpenInfra frontend application.

## Setup

Tests use Vitest with browser mode (Playwright provider). Dependencies are already installed.

**IMPORTANT**: Before running e2e tests, you must start the development server in a separate terminal:

```bash
# Terminal 1: Start the dev server
pnpm run dev

# Terminal 2: Run e2e tests
pnpm run test:e2e
```

The tests connect to `http://localhost:5173` (default Vite dev server port).

## Running Tests

### Run all tests
```bash
# Make sure dev server is running first!
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
- Setup file: `e2e/setup.ts`
- Test timeout: 30 seconds (increased for browser tests)
- Coverage: v8 provider with HTML reports
- Navigation: Uses `navigateTo` helper to avoid page reloads in browser mode

## Writing Tests

When writing new tests:

1. Use descriptive test names
2. Use `beforeEach` for common setup
3. Use `screen` from `@testing-library/react` for queries
4. Use `userEvent` for user interactions
5. Use `waitFor` to wait for async operations
6. **Use `navigateTo` helper from `./helpers` for navigation** (DO NOT use `window.location.href` as it causes page reloads)
7. Use `document.querySelector` for DOM queries when needed

Example:
```typescript
import { test, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { navigateTo } from './helpers';

test('should do something', async () => {
  // Use navigateTo helper instead of window.location.href
  await navigateTo('/page');
  await waitFor(() => document.body, { timeout: 5000 });

  const button = screen.queryByRole('button', { name: /click me/i });
  if (button) {
    await userEvent.click(button);
    await waitFor(() => {
      expect(window.location.pathname).toMatch(/.*success/);
    }, { timeout: 5000 });
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

- **Dev server must be running**: Tests connect to `http://localhost:5173`
- Some tests may skip if authentication is required (they check for login redirect)
- Map tests wait for map to load (5 seconds timeout)
- API-dependent tests may need mocking in the future
- Tests use flexible selectors to be resilient to UI changes
- Browser mode requires Playwright browsers to be installed (run `pnpm exec playwright install` if needed)
- **Never use `window.location.href` in tests** - it causes page reloads and breaks Vitest's iframe connection. Use `navigateTo()` helper instead.
