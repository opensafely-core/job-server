const alerts = document.querySelectorAll(`[role="alert"]`);

if (alerts.length) {
  [...alerts].map((alert) => {
    const closeBtn = alert.querySelector('button[aria-label="Close"]');

    if (closeBtn) {
      // Don't animate removal for users who prefer less motion
      const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      if (mediaQuery.matches) {
        return closeBtn.addEventListener("click", () => {
          alert.remove();
        });
      }

      return closeBtn.addEventListener("click", () => {
        alert.classList.add(
          "transition-all",
          "scale-100",
          "opacity-100",
          "duration-300",
        );

        alert.classList.remove("opacity-100", "scale-100");
        alert.classList.add("opacity-0", "scale-0");

        setTimeout(() => {
          alert.remove();
        }, 300);
      });
    }

    return null;
  });
}
