import * as Sentry from "@sentry/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "../../styles/outputs-viewer.scss";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

const element = document.getElementById("outputsSPA");
const root = createRoot(element);

root.render(
  <React.StrictMode>
    <BrowserRouter basename={element.dataset.basePath}>
      <QueryClientProvider client={queryClient}>
        <App {...element.dataset} element={element} />
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>
);
