import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

if (
  process.env.NODE_ENV === "production" &&
  import.meta.env.VITE_REACT_SENTRY
) {
  Sentry.init({
    dsn: import.meta.env.VITE_REACT_SENTRY,
    tracesSampleRate: 1.0,
  });
}

const element = document.getElementById("outputsSPA");

ReactDOM.render(
  <React.StrictMode>
    <App
      csrfToken={element.dataset.csrfToken}
      filesUrl={element.dataset.filesUrl}
      prepareUrl={element.dataset.prepareUrl}
    />
  </React.StrictMode>,
  element
);
