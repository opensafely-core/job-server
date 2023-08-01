/* eslint-disable no-console, import/no-extraneous-dependencies, react/prop-types */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { createMemoryHistory } from "history";
import * as React from "react";
import { unstable_HistoryRouter as HistoryRouter } from "react-router-dom";

export const history = createMemoryHistory({ window });

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        // ✅ turns retries off
        retry: false,
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      // ✅ no more errors on the console
      error: () => {},
    },
  });

function createWrapper() {
  const testQueryClient = createTestQueryClient();
  return ({ children }) => (
    <HistoryRouter history={history}>
      <QueryClientProvider client={testQueryClient}>
        {children}
      </QueryClientProvider>
    </HistoryRouter>
  );
}

const customRender = (ui, options) =>
  render(ui, {
    wrapper: createWrapper(),
    ...options,
  });

// re-export everything
export * from "@testing-library/react";

// override render method
export { customRender as render };
