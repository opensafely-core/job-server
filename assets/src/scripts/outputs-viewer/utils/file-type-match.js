export const isCsv = (fileName) =>
  fileName.toLowerCase().match(/.*\.(?:csv)$/i);

export const isHtml = (fileName) =>
  fileName.toLowerCase().match(/.*\.(?:html)$/i);

export const isImg = (fileName) =>
  fileName.toLowerCase().match(/.*\.(?:gif|jpg|jpeg|png|svg)$/i);

export const isTxt = (fileName) =>
  fileName.toLowerCase().match(/.*\.(?:txt)$/i);

export const isJson = (fileName) =>
  fileName.toLowerCase().match(/.*\.(?:json)$/i);

export const canDisplay = (fileName) =>
  isCsv(fileName) ||
  isHtml(fileName) ||
  isImg(fileName) ||
  isTxt(fileName) ||
  isJson(fileName);

export const isNotUploadedStr = `"File not yet uploaded"`;
