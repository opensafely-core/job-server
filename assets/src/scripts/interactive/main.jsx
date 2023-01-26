import * as Sentry from "@sentry/react";
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element = document.getElementById("osi");
const root = createRoot(element);

root.render(
  <React.StrictMode>
    <div>{console.log(element.dataset)}</div>
    {/* <BrowserRouter basename={element.dataset.basePath}> */}
    {/* <App {...element.dataset} element={element} /> */}
    {/* </BrowserRouter> */}
  </React.StrictMode>
);
