import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

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
