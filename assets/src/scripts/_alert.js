const alerts = document.querySelectorAll(`[role="alert"]`);

if (alerts.length) {
  [...alerts].map((alert) => {
    const closeBtn = alert.querySelector('button[aria-label="Close"]');

    if (closeBtn) {
      return closeBtn.addEventListener("click", () => {
        alert.classList.add(
          "transition-all",
          "scale-100",
          "opacity-100",
          "duration-300"
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
