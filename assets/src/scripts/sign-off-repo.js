const confirmDialog = document.getElementById("confirmDialog");
const confirmBtn = document.getElementById("confirmBtn");
const cancelBtn = confirmDialog.querySelector(`[value="cancel"]`);

confirmDialog.classList.add("hidden");

confirmBtn.addEventListener("click", () => {
  confirmDialog.classList.remove("hidden");
  confirmDialog.showModal();
});

cancelBtn.addEventListener("click", () => {
  confirmDialog.classList.add("hidden");
  confirmDialog.close("Cancelled");
});
