/* global $ */
import "../styles/main.scss";
import "./utils/double-click";

if (document.location.hostname === "jobs.opensafely.org") {
  const script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "jobs.opensafely.org");
  script.id = "plausible";
  script.src = "https://plausible.io/js/plausible.compat.js";

  document.head.appendChild(script);
}

if (document.getElementById("eventLog")) {
  document.querySelectorAll('[data-toggle="show-hide-btn"]').forEach((btn) => {
    btn.addEventListener("click", () => {
      const childRow = document.getElementById(
        btn.getAttribute("aria-controls")
      );

      if (childRow.hidden) {
        childRow.hidden = false;
        childRow.setAttribute("aria-hidden", false);
        return btn.setAttribute("aria-expanded", true);
      }

      childRow.hidden = true;
      childRow.setAttribute("aria-hidden", true);
      return btn.setAttribute("aria-expanded", false);
    });
  });

  $(() => {
    $('[data-toggle="tooltip"]').tooltip();
  });
}
