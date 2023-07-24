/* eslint-disable no-restricted-syntax */

const updateStatuses = (urlBase) => {
  /**
   * Update statuses for the current Workspace
   */

  // if a backend radio button has been checked use it filter the API query
  const checkedBackends = Array.from(
    document.getElementsByName("backend"),
  ).filter((e) => e.checked);
  let backendQuery = "";
  if (checkedBackends.length > 0) {
    backendQuery = `?backend=${checkedBackends[0].value}`;
  }

  const url = `${urlBase}${backendQuery}`;
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      const actions = document.querySelectorAll("#actions .card>.card-header");

      // loop the actions we've loaded from GitHub clearing their icon then
      // setting an icon if we get a status for them
      for (const action of actions) {
        // reset status icon
        const icon = action.querySelector(".status-icon");
        icon.className = "status-icon";

        const actionName = action.querySelector("code").title;
        const status = data[actionName];
        if (status) {
          // the API has a status for this action, update the icon
          icon.setAttribute("title", status);
          icon.className = `status-icon ${status}`;
        }
      }
    });
};

const urlBase = document.getElementById("apiUrl").textContent;

// run this on page load
updateStatuses(urlBase);

// poll the backend every 10s
window.setInterval(updateStatuses, 10000, urlBase);
