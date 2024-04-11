/* v8 ignore start */
import * as Sentry from "@sentry/react";
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element = document.getElementById("outputsSPA");
const root = createRoot(element);

if (document.getElementById("content")) {
  document.getElementById("content").remove();
}

root.render(
  <React.StrictMode>
    <BrowserRouter basename={element.dataset.basePath}>
      <App {...element.dataset} element={element} />
    </BrowserRouter>
  </React.StrictMode>,
);
/* v8 ignore stop */
