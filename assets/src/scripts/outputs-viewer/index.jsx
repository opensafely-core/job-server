import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

const element = document.getElementById("outputsSPA");

ReactDOM.render(
  <React.StrictMode>
    <App dataset={element.dataset} />
  </React.StrictMode>,
  element
);
