/**
 * @param {Element | null} el
 * @param {number | null} state
 * @param {{ page: (arg0: any) => any; }} table
 */
function pageButtonState(el, state, table) {
  if (el) {
    if (state) {
      el.classList.remove("hidden");
      el.addEventListener("click", () => table.page(state));
    } else {
      el.classList.add("hidden");
    }
  }
}

function getPageButtons() {
  let nextPageBtn = document.querySelector(
    `[data-table-pagination="next-page"]`,
  );
  nextPageBtn?.replaceWith(nextPageBtn.cloneNode(true));
  nextPageBtn = document.querySelector(`[data-table-pagination="next-page"]`);

  let previousPageBtn = document.querySelector(
    `[data-table-pagination="previous-page"]`,
  );
  previousPageBtn?.replaceWith(previousPageBtn.cloneNode(true));
  previousPageBtn = document.querySelector(
    `[data-table-pagination="previous-page"]`,
  );

  return { nextPageBtn, previousPageBtn };
}

/**
 * @param {number} currentPage
 * @param {import("simple-datatables").DataTable} table
 */
function setPaginationButtons(currentPage, table) {
  const pageNumberEl = document.querySelector(
    `[data-table-pagination="page-number"]`,
  );
  const totalPagesEl = document.querySelector(
    `[data-table-pagination="total-pages"]`,
  );

  const { nextPageBtn, previousPageBtn } = getPageButtons();
  const totalPages = table.pages.length;
  const pagination = {
    currentPage,
    totalPages,
    nextPage: currentPage < totalPages ? currentPage + 1 : null,
    previousPage: currentPage > 1 ? currentPage - 1 : null,
  };

  if (pageNumberEl) {
    pageNumberEl.innerHTML = JSON.stringify(pagination.currentPage);
  }
  if (totalPagesEl) {
    totalPagesEl.innerHTML = JSON.stringify(pagination.totalPages);
  }

  pageButtonState(nextPageBtn, pagination.nextPage, table);
  pageButtonState(previousPageBtn, pagination.previousPage, table);
}

(async () => {
  /** @type {HTMLTableElement | null} */
  const tableEl = document.querySelector("table#customTable");

  if (tableEl) {
    const { DataTable } = await import("simple-datatables");
    // @ts-ignore
    await import("../styles/_datatable.css");

    const dataTable = new DataTable(tableEl, {
      paging: true,
      perPage: 25,
      searchable: true,
      sortable: true,
      tableRender: (_data, table) => {
        const tHead = table.childNodes?.[0];
        const filterHeaders = {
          nodeName: "TR",
          childNodes: tHead?.childNodes?.[0].childNodes?.map((_th, index) => ({
            nodeName: "TH",
            childNodes: [
              {
                nodeName: "INPUT",
                attributes: {
                  class: "datatable-input",
                  "data-columns": `[${index}]`,
                  // @ts-ignore
                  placeholder: `Filter ${_data.headings[index].text
                    .trim()
                    .toLowerCase()}`,
                  type: "search",
                },
              },
            ],
          })),
        };
        tHead?.childNodes?.push(filterHeaders);
        return table;
      },
      template: (options) => `<div class='${options.classes.container}'></div>`,
    });

    /** @type {NodeListOf<HTMLInputElement>} */
    const filters = document.querySelectorAll("input.datatable-input");
    [...filters].map((filter) => {
      filter.addEventListener("input", () => {
        if (filter?.value === "") {
          return setTimeout(() => setPaginationButtons(1, dataTable), 0);
        }
        return null;
      });
      return null;
    });

    dataTable.on("datatable.init", () => setPaginationButtons(1, dataTable));
    dataTable.on("datatable.page", (/** @type {number} */ page) =>
      setPaginationButtons(page, dataTable),
    );
    dataTable.on("datatable.sort", () => setPaginationButtons(1, dataTable));
    dataTable.on("datatable.search", () => setPaginationButtons(1, dataTable));
  }
})();
