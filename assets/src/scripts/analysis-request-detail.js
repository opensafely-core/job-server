const report = document.querySelector("#reportContainer");
const downloadBtn = document.querySelector("#downloadBtn");
const watermark = document.querySelector("#watermark");

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

downloadBtn.addEventListener("click", async () => {
  // Load the JS on button click
  const html2pdf = await import("html2pdf.js");

  // Repeat the watermark 300 times on the container
  const singleInner = watermark.innerHTML;
  watermark.classList.remove("hidden");
  watermark.innerHTML = watermark.innerHTML.repeat(300);

  // Generate and download the PDF
  html2pdf.default().set(options).from(report).toContainer().toPdf().save();

  // 0 timeout to remove watermark after the event loop has finished
  setTimeout(() => {
    watermark.classList.add("hidden");
    watermark.innerHTML = singleInner;
  }, 0);
});
