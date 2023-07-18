import "../../../templates/interactive/analysis_request_detail.css";

function generatePDF() {
  const downloadBtn = document.getElementById("downloadBtn");

  const reportContainer = document.getElementById("reportContainer");
  const watermark = reportContainer.querySelector("#watermark");
  const report = reportContainer.querySelector("#report");

  const viewPurposeLink = document.getElementById("viewProjectPurposeLink");
  const viewOnOSLink = document.getElementById("viewOnOpensafelyLink");

  const downloadModal = document.getElementById("downloadModal");
  const confirmBtn = downloadModal.querySelector(`[value="confirm"]`);
  const cancelBtn = downloadModal.querySelector(`[value="cancel"]`);
  const generatingBtn = downloadModal.querySelector(`[value="generating"]`);
  const downloadingBtn = downloadModal.querySelector(`[value="downloading"]`);

  const options = {
    margin: 15,
    filename: `${downloadBtn.dataset.title} - Report.pdf`,
    image: { type: "jpeg", quality: 0.75 },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    html2canvas: {
      scale: 2,
    },
    pagebreak: { mode: "avoid-all" },
  };

  let pdf;

  downloadBtn.addEventListener("click", async () => {
    downloadModal.showModal();

    // Load the JS on button click
    const html2pdf = await import("html2pdf.js");

    // Reset the styles for printing
    report.classList.add(`print-pdf`);

    // flip the links
    viewPurposeLink.classList.add("hidden");
    viewOnOSLink.classList.remove("hidden");

    // Remove elements not required
    reportContainer
      .querySelectorAll("svg")
      .forEach((element) => element.classList.add("!hidden"));
    reportContainer.querySelector(".toc").classList.add("!hidden");

    // Repeat the watermark 300 times on the container
    const singleInner = watermark.innerHTML;
    watermark.classList.remove("hidden");
    watermark.innerHTML = watermark.innerHTML.repeat(300);

    // Generate and download the PDF
    pdf = html2pdf.default().set(options).from(report).toContainer().toPdf();
    await pdf;

    // 0 timeout to remove watermark after the event loop has finished
    setTimeout(() => {
      watermark.classList.add("hidden");
      watermark.innerHTML = singleInner;
      report.classList.remove(`print-pdf`);
      reportContainer
        .querySelectorAll("svg")
        .forEach((element) => element.classList.remove("!hidden"));
      reportContainer.querySelector(".toc").classList.remove("!hidden");
    }, 0);

    // flip the links back
    viewOnOSLink.classList.add("hidden");
    viewPurposeLink.classList.remove("hidden");

    // Show download button
    confirmBtn.classList.remove("hidden");
    generatingBtn.classList.add("hidden");
  });

  confirmBtn.addEventListener("click", () => {
    // When confirm is clicked, save the PDF
    pdf.save();

    // Switch the buttons
    confirmBtn.classList.add("hidden");
    generatingBtn.classList.add("hidden");
    downloadingBtn.classList.remove("hidden");

    // Wait 1s then close the dialog
    setTimeout(() => {
      // Reset the buttons
      confirmBtn.classList.add("hidden");
      downloadingBtn.classList.add("hidden");
      generatingBtn.classList.remove("hidden");

      downloadModal.close("Download started");
    }, 1000);
  });

  cancelBtn.addEventListener("click", () => {
    downloadModal.close("Download cancelled");

    // Reset the buttons
    confirmBtn.classList.add("hidden");
    downloadingBtn.classList.add("hidden");
    generatingBtn.classList.remove("hidden");
  });
}

function formatNumbers() {
  const numbers = document.querySelectorAll(`[data-format-number="true"]`);
  numbers?.forEach(
    // eslint-disable-next-line no-return-assign
    (number) =>
      // eslint-disable-next-line no-param-reassign
      (number.textContent = parseFloat(number.textContent).toLocaleString(
        "en-GB",
      )),
  );
}

function addMenuButton() {
  if (document.querySelector("#tableOfContents")) {
    const menuBtn = document.createElement("a");
    menuBtn.id = "menuBtn";
    menuBtn.textContent = "Back to table of contents";
    menuBtn.href = "#tableOfContents";
    document.querySelector("main").appendChild(menuBtn);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  generatePDF();
  formatNumbers();
  addMenuButton();
});
