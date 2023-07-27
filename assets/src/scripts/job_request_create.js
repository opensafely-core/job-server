function getBackendValue() {
  const backend = document.querySelector(`#backends input:checked`);
  return backend?.value ? `?backend=${backend.value}` : ``;
}

async function getStatuses() {
  const urlBase = document.querySelector(`meta[name="apiUrl"]`).content;
  const response = await fetch(`${urlBase}${getBackendValue()}`);

  if (!response.ok) {
    const message = `An error has occurred: ${response.status}`;
    throw new Error(message);
  }

  const statuses = await response.json();
  return statuses;
}

async function setActionsStatuses() {
  const actions = [...document.querySelectorAll(`#jobActions label`)];
  const statuses = await getStatuses();

  actions.map((action) => {
    const actionName = action.textContent.trim();
    const status = statuses[actionName];
    const parentEl = action.closest(`#jobActions`);
    const loadingIcon = parentEl.querySelector(
      `[data-action-status="loading"]`,
    );
    const successIcon = parentEl.querySelector(
      `[data-action-status="succeeded"]`,
    );
    const failedIcon = parentEl.querySelector(`[data-action-status="failed"]`);

    if (status === "succeeded") {
      loadingIcon.classList.add("hidden");
      failedIcon.classList.add("hidden");
      return successIcon.classList.remove("hidden");
    }

    if (status === "failed") {
      loadingIcon.classList.add("hidden");
      successIcon.classList.add("hidden");
      return failedIcon.classList.remove("hidden");
    }

    failedIcon.classList.add("hidden");
    successIcon.classList.add("hidden");
    return loadingIcon.classList.remove("hidden");
  });
}

setActionsStatuses();
