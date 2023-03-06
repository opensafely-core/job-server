if (document.location.hostname === "jobs.opensafely.org") {
  const script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "jobs.opensafely.org");
  script.id = "plausible";
  script.src = "https://plausible.io/js/plausible.compat.js";

  document.head.appendChild(script);
}
