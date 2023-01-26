import * as Sentry from "@sentry/react";
import React from "react";
import { createRoot } from "react-dom/client";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element = document.getElementById("osi");
const root = createRoot(element as HTMLElement);

// eslint-disable-next-line no-console
console.log({ element });

root.render(
  <React.StrictMode>
    <h1>Silence is golden</h1>
  </React.StrictMode>
);
