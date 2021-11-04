/* eslint-disable no-console, import/no-extraneous-dependencies */
import { render } from "@testing-library/react";
import { createMemoryHistory } from "history";
import React from "react";
import { QueryClient, QueryClientProvider, setLogger } from "react-query";
import { Router } from "react-router-dom";
import { FilesProvider } from "../context/FilesProvider";

export const history = createMemoryHistory();

const createWrapper =
  ({ filesContext } = {}) =>
  // eslint-disable-next-line react/prop-types
  ({ children }) => {
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
      <FilesProvider
        initialValue={{
          authToken: "",
          basePath: "",
          csrfToken: "",
          filesUrl: "",
          prepareUrl: "",
          publishUrl: "",
          ...filesContext,
        }}
      >
        <Router history={history}>
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        </Router>
      </FilesProvider>
    );
  };

export const wrapper = createWrapper();

const customRender = (ui, options, filesContext) =>
  render(ui, {
    wrapper: createWrapper({ filesContext }),
    ...options,
  });

// re-export everything
export * from "@testing-library/react";

// override render method
export { customRender as render };
