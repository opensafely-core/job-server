import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

const element = document.getElementById("outputsSPA");

ReactDOM.render(
  <React.StrictMode>
    <App filesUrl={element.dataset.filesUrl} />
  </React.StrictMode>,
  element
);
