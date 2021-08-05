export const isCsv = (file) => file.name.toLowerCase().match(/.*\.(?:csv)$/i);

export const isHtml = (file) => file.name.toLowerCase().match(/.*\.(?:html)$/i);

export const isImg = (file) =>
  file.name.toLowerCase().match(/.*\.(?:gif|jpg|jpeg|png|svg)$/i);

export const isTxt = (file) => file.name.toLowerCase().match(/.*\.(?:txt)$/i);

export const isJson = (file) => file.name.toLowerCase().match(/.*\.(?:json)$/i);

export const canDisplay = (file) =>
  isCsv(file) || isHtml(file) || isImg(file) || isTxt(file) || isJson(file);
