import { DataTable } from "simple-datatables";
import "../styles/_datatable.css";

const tableEl = document.getElementById("customTable");

const template = (options) =>
  `<div class='${options.classes.container}'></div>`;

const opts = {
  paging: true,
  perPage: 25,
  searchable: true,
  sortable: true,
  perPageSelect: false,
  template,
  tableRender: (_data, table) => {
    const tHead = table.childNodes[0];
    const filterHeaders = {
      nodeName: "TR",
      childNodes: tHead.childNodes[0].childNodes.map((_th, index) => ({
        nodeName: "TH",
        childNodes: [
          {
            nodeName: "INPUT",
            attributes: {
              class: "datatable-input",
              "data-columns": `[${index}]`,
              placeholder: "Filter column",
              type: "search",
            },
          },
        ],
      })),
    };
    tHead.childNodes.push(filterHeaders);
    return table;
  },
};

const dataTable = new DataTable(tableEl, opts);

const pageNumberEl = document.querySelector(
  `[data-table-pagination="page-number"]`,
);
const totalPagesEl = document.querySelector(
  `[data-table-pagination="total-pages"]`,
);

function pageButtonState(el, state) {
  if (state) {
    el.classList.remove("hidden");
    el.addEventListener("click", () => dataTable.page(state));
  } else {
    el.classList.add("hidden");
  }
}

function getPageButtons() {
  let nextPageBtn = document.querySelector(
    `[data-table-pagination="next-page"]`,
  );
  nextPageBtn.replaceWith(nextPageBtn.cloneNode(true));
  nextPageBtn = document.querySelector(`[data-table-pagination="next-page"]`);

  let previousPageBtn = document.querySelector(
    `[data-table-pagination="previous-page"]`,
  );
  previousPageBtn.replaceWith(previousPageBtn.cloneNode(true));
  previousPageBtn = document.querySelector(
    `[data-table-pagination="previous-page"]`,
  );

  return { nextPageBtn, previousPageBtn };
}

function setPaginationButtons(currentPage) {
  const { nextPageBtn, previousPageBtn } = getPageButtons();
  const totalPages = dataTable.pages.length;
  const pagination = {
    currentPage,
    totalPages,
    nextPage: currentPage < totalPages ? currentPage + 1 : null,
    previousPage: currentPage > 1 ? currentPage - 1 : null,
  };

  pageNumberEl.innerHTML = pagination.currentPage;
  totalPagesEl.innerHTML = pagination.totalPages;
  pageButtonState(nextPageBtn, pagination.nextPage);
  pageButtonState(previousPageBtn, pagination.previousPage);
}

dataTable.on("datatable.init", () => setPaginationButtons(1));
dataTable.on("datatable.page", (page) => setPaginationButtons(page));
dataTable.on("datatable.search", () => {
  document.querySelector(`[data-table-pagination="page-number"]`).innerHTML = 1;
  setPaginationButtons(1);
});
