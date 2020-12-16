const updateStatuses = (url) => {
  /**
   * Update statuses for the current Workspace
   */
  fetch(url)
    .then(response => response.json())
    .then(data => {
      for (const [action, status] of Object.entries(data)) {
        const icon = document.querySelector(`#heading-${action} .status-icon`);

        if (icon === null) {
          // icon can be null when we have jobs for an action which was
          // previously in the project.yaml but has since been removed.
          continue;
        }

        icon.setAttribute("title", status);
        icon.className = `status-icon ${status}`;
      }
    });
}
window.addEventListener("DOMContentLoaded", () => {
  const url = document.getElementById("apiUrl").textContent;

  // poll the backend every 10s
  window.setInterval(updateStatuses, 10000, url);
});
