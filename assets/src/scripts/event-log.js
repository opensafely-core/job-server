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
