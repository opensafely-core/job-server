/* global $ */
// Bootstrap tooltips
import hljs from "highlight.js/lib/core";
import json from "highlight.js/lib/languages/json";
import "highlight.js/styles/github.css";

$(() => {
  $('[data-toggle="tooltip"]').tooltip();
});

hljs.registerLanguage("json", json);

const analysisRequest = document.getElementById("analysisRequest");

if (analysisRequest) {
  analysisRequest.textContent = JSON.stringify(
    JSON.parse(document.getElementById("analysisRequestData").textContent),
    null,
    2
  );
}

hljs.highlightAll();
