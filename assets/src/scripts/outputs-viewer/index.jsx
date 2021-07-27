import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

if (
  process.env.NODE_ENV === "production" &&
  document.location.hostname === "jobs.opensafely.org"
) {
  Sentry.init({
    dsn: "https://adf34e0d9a5445fea760b43cf10ad45b@o173701.ingest.sentry.io/5881265",
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
