/**
 * Return a querystring for the selected backend
 * @returns {string} - query string for backend, or empty string
 */
function getBackendValue() {
  const backend = /** @type {HTMLInputElement|null} */ document.querySelector(
    `#backends input:checked`,
  );
  return backend?.value ? `?backend=${backend.value}` : ``;
}

/**
 * Fetch the status for the jobs based on the meta tag and backend query string
 * @returns {Promise<object>} - JSON object containing statuses
 */
async function getStatuses() {
  const urlBase =
    /** @type {HTMLMetaElement} */ document.querySelector(
      `meta[name="apiUrl"]`,
    )?.content;
  const response = await fetch(`${urlBase}${getBackendValue()}`);

  if (!response.ok) {
    const message = `An error has occurred: ${response.status}`;
    throw new Error(message);
  }

  const statuses = await response.json();
  return statuses;
}

/**
 * Set the visible icon based on the status returned from the API
 * @param {HTMLLabelElement} action - label element for an action
 * @param {("succeeded"|"failed"|"loading")} status - status returned from the API
 * @returns {void}
 */
function setIcon(action, status) {
  const parentEl = action.closest(`#jobActions`);
  const loadingIcon = parentEl?.querySelector(`[data-action-status="loading"]`);
  const successIcon = parentEl?.querySelector(
    `[data-action-status="succeeded"]`,
  );
  const failedIcon = parentEl?.querySelector(`[data-action-status="failed"]`);

  if (status === "succeeded") {
    loadingIcon?.classList.add("hidden");
    failedIcon?.classList.add("hidden");
    return successIcon?.classList.remove("hidden");
  }

  if (status === "failed") {
    loadingIcon?.classList.add("hidden");
    successIcon?.classList.add("hidden");
    return failedIcon?.classList.remove("hidden");
  }

  failedIcon?.classList.add("hidden");
  successIcon?.classList.add("hidden");
  return loadingIcon?.classList.remove("hidden");
}

async function setActionsStatuses() {
  const actions = [...document.querySelectorAll(`#jobActions label`)];
  actions.map((action) => setIcon(action, "loading"));

  const statuses = await getStatuses();

  actions.map((action) => {
    const actionName = action.textContent.trim();
    const status = statuses[actionName];
    return setIcon(action, status);
  });
}

/**
 * Re-run the function to check the status when the user focusses the tab
 */
function handleVisibilityChange() {
  if (document.visibilityState === "visible") {
    setActionsStatuses();
  }
}
document.addEventListener("visibilitychange", handleVisibilityChange);

// Find the status on page load
setActionsStatuses();
