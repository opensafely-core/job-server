/* global $ */
// Bootstrap tooltips
import hljs from "highlight.js/lib/core";
import json from "highlight.js/lib/languages/json";
import "highlight.js/styles/github.css";

$(() => {
  $('[data-toggle="tooltip"]').tooltip();
});

hljs.registerLanguage("json", json);

document.getElementById("analysisRequest").textContent = JSON.stringify(
  JSON.parse(document.getElementById("analysisRequestData").textContent),
  null,
  2
);

hljs.highlightAll();
