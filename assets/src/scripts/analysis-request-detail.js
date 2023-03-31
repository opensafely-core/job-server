const downloadBtn = document.getElementById("downloadBtn");

const report = document.getElementById("reportContainer");
const watermark = report.querySelector("#watermark");
const reportStyles = report.querySelector("#report");

const dialog = document.getElementById("downloadModal");
const confirmBtn = dialog.querySelector(`[value="confirm"]`);
const cancelBtn = dialog.querySelector(`[value="cancel"]`);
const generatingBtn = dialog.querySelector(`[value="generating"]`);

const options = {
  margin: 20,
  filename: `${downloadBtn.dataset.title} - Report.pdf`,
  image: { type: "jpeg", quality: 0.75 },
  jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
  html2canvas: {
    ignore: () => report.querySelector("svg"),
    scale: 2,
  },
};

let pdf;

downloadBtn.addEventListener("click", async () => {
  dialog.showModal();

  // Load the JS on button click
  const html2pdf = await import("html2pdf.js");

  // Restore the h1 for the printed report
  reportStyles.classList.remove(`[&_h1]:hidden`);

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
    reportStyles.classList.add(`[&_h1]:hidden`);
  }, 0);

  // Show download button
  confirmBtn.classList.remove("hidden");
  generatingBtn.remove();
});

confirmBtn.addEventListener("click", () => {
  // When confirm is clicked, save the PDF
  pdf.save();

  // Wait 1s then close the dialog
  setTimeout(() => dialog.close(), 1000);
});

cancelBtn.addEventListener("click", () => {
  dialog.close();
});
