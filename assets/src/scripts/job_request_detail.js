document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("jobs-filter-status");
  const emptyState = document.getElementById("jobs-empty-state");
  const rows = document.querySelectorAll("#jobs-list li[data-status]");

  if (!select || !emptyState) return;

  function applyFilter() {
    const status = select.value;
    let visibleCount = 0;

    for (const row of rows) {
      const visible = status ? row.dataset.status === status : true;
      row.hidden = !visible;
      if (visible) visibleCount += 1;
    }

    emptyState.hidden = status === "" || visibleCount > 0;
  }

  select.addEventListener("change", applyFilter);
  applyFilter();
});
