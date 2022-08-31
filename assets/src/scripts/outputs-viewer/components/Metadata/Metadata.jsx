import React from "react";
import prettyFileSize from "../../utils/pretty-file-size";
import { selectedFileProps } from "../../utils/props";

function Metadata({ fileDate, fileName, fileSize, fileUrl }) {
  const fileDateValue = () => {
    if (Date.parse(fileDate)) {
      const getDate = new Date(fileDate);

      return {
        absolute: getDate.toISOString(),
        formatted: new Intl.DateTimeFormat("en-GB", {
          timeZone: "UTC",
          dateStyle: "short",
          timeStyle: "short",
        }).format(getDate),
      };
    }
    return false;
  };

  return (
    <ul className="list-inline small text-monospace d-flex flex-column flex-md-row mb-0">
      <li className="list-inline-item mr-auto">
        <a
          className="file-link d-flex"
          href={fileUrl}
          rel="noreferrer noopener"
          target="filePreview"
        >
          {fileName}
        </a>
      </li>
      {fileDateValue() && (
        <li className="list-inline-item">
          <div className="sr-only">Last modified at: </div>
          <time
            className="file-date"
            dateTime={fileDateValue().absolute}
            title={fileDateValue().absolute}
          >
            {fileDateValue().formatted}
          </time>
        </li>
      )}
      <li className="list-inline-item spacer">{prettyFileSize(fileSize)}</li>
    </ul>
  );
}

export default Metadata;

Metadata.propTypes = {
  fileDate: selectedFileProps.date.isRequired,
  fileName: selectedFileProps.name.isRequired,
  fileSize: selectedFileProps.size.isRequired,
  fileUrl: selectedFileProps.url.isRequired,
};
