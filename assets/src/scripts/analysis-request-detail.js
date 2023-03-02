import * as html2pdf from "html2pdf.js";

const report = document.querySelector("#reportContainer");
const downloadBtn = document.querySelector("#downloadBtn");
const watermark = document.querySelector("#watermark");

const options = {
  margin: 2,
  filename: `${downloadBtn.dataset.title} - Report.pdf`,
  image: { type: "png" },
  jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
  html2canvas: {
    ignore: () => report.querySelector("svg"),
    scale: 2,
  },
};

downloadBtn.addEventListener("click", () => {
  watermark.classList.remove("hidden");
  const singleInner = watermark.innerHTML;
  watermark.innerHTML = watermark.innerHTML.repeat(300);

  html2pdf().set(options).from(report).toContainer().toPdf().save();

  setTimeout(() => {
    watermark.classList.add("hidden");
    watermark.innerHTML = singleInner;
  }, 0);
});
