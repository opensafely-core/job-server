(async () => {
  const analysisRequest = document.getElementById("analysisRequest");

  if (analysisRequest) {
    const hljs = (await import("highlight.js/lib/core")).default;
    const json = (await import("highlight.js/lib/languages/json")).default;
    await import("highlight.js/styles/github.css");

    hljs.registerLanguage("json", json);

    analysisRequest.textContent = JSON.stringify(
      JSON.parse(document.getElementById("analysisRequestData").textContent),
      null,
      2,
    );

    hljs.highlightAll();
  }
})();
