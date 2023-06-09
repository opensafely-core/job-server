/* global $ */
$(() => {
  $("table").tablesorter({
    theme: "bootstrap",
    widthFixed: true,
    sortReset: true,
    widgets: ["filter", "columns"],
    headers: {
      0: { sortInitialOrder: "desc" },
    },
    widgetOptions: {
      columns: ["table-info"],
      filter_reset: ".reset",
      filter_cssFilter: [
        "form-control",
        "form-control",
        "form-control",
        "form-control",
        "form-control",
        "form-control",
        "form-control",
        "form-control",
        "form-control",
      ],
    },
  });
});
