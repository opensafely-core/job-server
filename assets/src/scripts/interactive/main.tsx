import * as Sentry from "@sentry/react";
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element: HTMLElement | null = document.getElementById("osi");
if (!element) throw new Error("Failed to find the root element");

const root = createRoot(element);
const { dataset } = element;
if (!dataset.events || !dataset.medications)
  throw new Error("Codelist data not provided");

root.render(
  <React.StrictMode>
    <App events={dataset.events} medications={dataset.medications} />
  </React.StrictMode>
);
