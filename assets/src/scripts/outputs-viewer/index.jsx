import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";
import "../../styles/outputs-viewer.scss";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const element = document.getElementById("outputsSPA");

ReactDOM.render(
  <React.StrictMode>
    <App {...element.dataset} element={element} />
  </React.StrictMode>,
  element
);
