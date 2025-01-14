/* global $ */

if (document.getElementById("eventLog")) {
  document.querySelectorAll('[data-toggle="show-hide-btn"]').forEach((btn) => {
    btn.addEventListener("click", () => {
      const childRow = document.getElementById(
        btn.getAttribute("aria-controls"),
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

  // biome-ignore lint/correctness/noUndeclaredVariables: ESLint to Biome legacy ignore
  $(() => {
    // biome-ignore lint/correctness/noUndeclaredVariables: ESLint to Biome legacy ignore
    $('[data-toggle="tooltip"]').tooltip();
  });
}
