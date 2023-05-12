import "../../../templates/interactive/analysis_request_detail.css";

function generatePDF() {
  const downloadBtn = document.getElementById("downloadBtn");

  const report = document.getElementById("reportContainer");
  const watermark = report.querySelector("#watermark");
  const reportStyles = report.querySelector("#report");

  const dialog = document.getElementById("downloadModal");
  const confirmBtn = dialog.querySelector(`[value="confirm"]`);
  const cancelBtn = dialog.querySelector(`[value="cancel"]`);
  const generatingBtn = dialog.querySelector(`[value="generating"]`);
  const downloadingBtn = dialog.querySelector(`[value="downloading"]`);

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
    dialog.showModal();

    // Load the JS on button click
    const html2pdf = await import("html2pdf.js");

    // Reset the styles for printing
    reportStyles.classList.add(`print-pdf`);

    // Remove elements not required
    report
      .querySelectorAll("svg")
      .forEach((element) => element.classList.add("!hidden"));
    report.querySelector(".toc").classList.add("!hidden");

    // Repeat the watermark 300 times on the container
    const singleInner = watermark.innerHTML;
    watermark.classList.remove("hidden");
    watermark.innerHTML = watermark.innerHTML.repeat(300);

    // Generate and download the PDF
    pdf = html2pdf
      .default()
      .set(options)
      .from(reportStyles)
      .toContainer()
      .toPdf();
    await pdf;

    // 0 timeout to remove watermark after the event loop has finished
    setTimeout(() => {
      watermark.classList.add("hidden");
      watermark.innerHTML = singleInner;
      reportStyles.classList.remove(`print-pdf`);
      report
        .querySelectorAll("svg")
        .forEach((element) => element.classList.remove("!hidden"));
      report.querySelector(".toc").classList.remove("!hidden");
    }, 0);

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

      dialog.close("Download started");
    }, 1000);
  });

  cancelBtn.addEventListener("click", () => {
    dialog.close("Download cancelled");

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
        "en-GB"
      ))
  );
}

function addMenuButton() {
  if (document.querySelector("#tableOfContents")) {
    const menuBtn = document.createElement("a");
    menuBtn.id = "menuBtn";
    menuBtn.textContent = "Back to table of content";
    menuBtn.href = "#tableOfContents";
    document.querySelector("main").appendChild(menuBtn);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  generatePDF();
  formatNumbers();
  addMenuButton();
});
