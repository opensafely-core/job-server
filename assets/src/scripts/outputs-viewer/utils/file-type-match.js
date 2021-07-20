export const isCsv = (file) => file.name.match(/.*\.(?:csv)$/i);

export const isHtml = (file) => file.name.match(/.*\.(?:html)$/i);

export const isImg = (file) =>
  file.name.match(/.*\.(?:gif|jpg|jpeg|png|svg)$/i);

export const isTxt = (file) => file.name.match(/.*\.(?:txt)$/i);

export const canDisplay = (file) =>
  isCsv(file) || isHtml(file) || isImg(file) || isTxt(file);
