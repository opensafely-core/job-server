const triggers = [...document.querySelectorAll(`[data-modal]`)];
const modals = [...document.querySelectorAll(`dialog`)];

triggers.map((trigger) => {
  const modal = document.getElementById(trigger.dataset.modal);

  trigger?.addEventListener("click", (e) => {
    e.preventDefault();
    modal.showModal();
  });

  return true;
});

modals.map((modal) => {
  const cancelBtn = modal.querySelector(`[type="cancel"]`);
  cancelBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    modal.close();
  });

  return false;
});
