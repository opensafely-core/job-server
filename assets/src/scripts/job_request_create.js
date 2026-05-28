/**
 * Return a querystring for the selected backend
 * @returns {string} - query string for backend, or empty string
 */
function getBackendValue() {
  /** @type {HTMLInputElement|null} */
  const backend = document.querySelector(`#backends input:checked`);
  return backend?.value ? `?backend=${backend.value}` : ``;
}

/**
 * Fetch the status for the jobs based on the meta tag and backend query string
 * @returns {Promise<object>} - JSON object containing statuses
 */
async function getStatuses() {
  /** @type {HTMLMetaElement|null} */
  const apiUrl = document.querySelector(`meta[name="apiUrl"]`);
  const urlBase = apiUrl?.content;
  const response = await fetch(`${urlBase}${getBackendValue()}`);

  if (!response.ok) {
    const message = `An error has occurred: ${response.status}`;
    throw new Error(message);
  }

  const statuses = await response.json();
  return statuses;
}

/**
 * @typedef {"succeeded"|"failed"|"none"|"running"|"pending"|"loading"} StatusState
 */

/** @type {Record<StatusState, {className: string, label: string}>} */
const STATUS_STATES = {
  succeeded: {
    className: "pill--success",
    label: "Succeeded",
  },
  failed: {
    className: "pill--failed",
    label: "Failed",
  },
  none: {
    className: "pill--info",
    label: "No status",
  },
  loading: {
    className: "pill--info",
    label: "Loading",
  },
};

/**
 * Set the visible icon based on the status returned from the API
 * @param {Element} action - label element for an action
 * @param {StatusState|string} status - status returned from the API
 * @returns {void}
 */
function setIcon(action, status) {
  const parentEl = action.closest(`[data-action]`);
  const pill = parentEl.querySelector("[data-action-status]");
  const state = STATUS_STATES[status] || STATUS_STATES.loading;

  pill.classList.remove(
    ...[...pill.classList].filter((className) =>
      className.startsWith("pill--"),
    ),
  );
  pill.classList.add(state.className);
  pill.textContent = state.label;
}

async function setActionsStatuses() {
  const actions = [...document.querySelectorAll(`[data-action] label`)];
  actions.map((action) => setIcon(action, "loading"));

  const statuses = await getStatuses();

  actions.map((action) => {
    const actionName = action?.textContent?.trim();
    const status = statuses?.[actionName] || "none";
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
