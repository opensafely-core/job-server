import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";
import { FilesProvider } from "./context/FilesProvider";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element = document.getElementById("outputsSPA");

ReactDOM.render(
  <React.StrictMode>
    <FilesProvider
      initialValue={{
        authToken: element.dataset.authToken,
        basePath: element.dataset.basePath,
        csrfToken: element.dataset.csrfToken,
        filesUrl: element.dataset.filesUrl,
        prepareUrl: element.dataset.prepareUrl,
        publishUrl: element.dataset.publishUrl,
      }}
    >
      <App element={element} />
    </FilesProvider>
  </React.StrictMode>,
  element
);
