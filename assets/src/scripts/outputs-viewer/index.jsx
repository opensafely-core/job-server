import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";
import useStore from "./stores/use-store";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element = document.getElementById("outputsSPA");

useStore.setState({
  authToken: element.dataset.authToken,
  basePath: element.dataset.basePath,
  csrfToken: element.dataset.csrfToken,
  filePath: element.dataset.filePath,
  filesUrl: element.dataset.filesUrl,
  prepareUrl: element.dataset.prepareUrl,
  publishUrl: element.dataset.publishUrl,
});

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  element
);
