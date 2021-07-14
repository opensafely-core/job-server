import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

const element = document.getElementById("outputsSPA");

ReactDOM.render(
  <React.StrictMode>
    <App apiUrl={element.dataset.apiUrl} />
  </React.StrictMode>,
  element
);
