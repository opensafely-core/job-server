/* eslint-disable no-console, import/no-extraneous-dependencies */
import { render } from "@testing-library/react";
import { createMemoryHistory } from "history";
import React from "react";
import { QueryClient, QueryClientProvider, setLogger } from "react-query";
import { Router } from "react-router-dom";

export const history = createMemoryHistory();

export const wrapper = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        // ✅ turns retries off
        retry: false,
      },
    },
  });

  setLogger({
    log: console.log,
    warn: console.warn,
    // ✅ no more errors on the console
    error: () => {},
  });

  return (
    <Router history={history}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </Router>
  );
};

const customRender = (ui, options) => render(ui, { wrapper, ...options });

// re-export everything
export * from "@testing-library/react";

// override render method
export { customRender as render };
