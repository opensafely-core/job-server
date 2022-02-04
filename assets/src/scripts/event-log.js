/* global $ */

$(() => {
  const selects = [
    { id: "filter_backend", placeholder: "Backend" },
    { id: "filter_status", placeholder: "Status" },
    { id: "filter_user", placeholder: "User" },
    { id: "filter_workspace", placeholder: "Workspace" },
  ];

  selects.forEach((select) => {
    $(`#${select.id}`).select2({
      placeholder: select.placeholder,
      selectionCssClass: ":all:",
      theme: "bootstrap4",
    });
  });
});

const modalsBtns = document.querySelectorAll('[data-toggle="modal"]');

modalsBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    const workspaceName = btn.getAttribute("data-workspace-name");
    const workspaceContentName = btn.getAttribute("data-workspace-content");
    const workspaceContentHTML =
      document.getElementById(workspaceContentName).innerHTML;

    document.getElementById("jobModalTitle").textContent = workspaceName;
    document.getElementById("jobModalBody").innerHTML = workspaceContentHTML;
  });
});
