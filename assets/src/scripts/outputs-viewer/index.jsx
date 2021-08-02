import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element = document.getElementById("outputsSPA");

ReactDOM.render(
  <React.StrictMode>
    <App
      csrfToken={element.dataset.csrfToken}
      filesUrl={element.dataset.filesUrl}
      prepareUrl={element.dataset.prepareUrl}
      publishUrl={element.dataset.publishUrl}
    />
  </React.StrictMode>,
  element
);
