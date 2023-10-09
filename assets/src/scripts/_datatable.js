import { DataTable } from "simple-datatables";
import "../styles/_datatable.css";

const tableEl = document.getElementById("customTable");

const template = (options) => `<div class='${
  options.classes.top
} fixed-table-toolbar'>
  ${
    options.paging && options.perPageSelect
      ? `<div class='${options.classes.dropdown} bs-bars float-left'>
          <label>
              <select class='${options.classes.selector}'></select>
          </label>
      </div>`
      : ""
  }
</div>
<div class='${options.classes.container}'${
  options.scrollY.length
    ? ` style='height: ${options.scrollY}; overflow-Y: auto;'`
    : ""
}></div>`;

const opts = {
  paging: true,
  perPage: 25,
  searchable: true,
  sortable: true,
  perPageSelect: false,
  template,
  tableRender: (_data, table, type) => {
    if (type === "print") {
      return table;
    }
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
const nextPageBtn = document.querySelector(
  `[data-table-pagination="next-page"]`,
);

const firstPageClick = () => {
  if (dataTable.pages.length > 1) {
    dataTable.page(2);
  }
};

dataTable.on("datatable.init", () => {
  const pageNum = 1;
  pageNumberEl.innerHTML = pageNum;
  totalPagesEl.innerHTML = dataTable.pages.length;

  nextPageBtn.addEventListener("click", firstPageClick);
});

dataTable.on("datatable.page", (page) => {
  const pageNum = page;
  pageNumberEl.innerHTML = pageNum;
  totalPagesEl.innerHTML = dataTable.pages.length;

  for (const eventType in getEventListeners(nextPageBtn)) {
    getEventListeners(nextPageBtn)[eventType].forEach((o) => {
      o.remove();
    });
  }
  nextPageBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (dataTable.pages.length > pageNum) {
      dataTable.page(pageNum + 1);
    }
  });
});

dataTable.on("datatable.search", (query, matched) => {
  document.querySelector(`[data-table-pagination="page-number"]`).innerHTML = 1;
  totalPagesEl.innerHTML = dataTable.pages.length;
});
