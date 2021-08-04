import prettyBytes from "pretty-bytes";

function prettyFileSize(fileSize) {
  return fileSize ? prettyBytes(fileSize, { locale: "en-gb" }) : "unknown";
}

export default prettyFileSize;
