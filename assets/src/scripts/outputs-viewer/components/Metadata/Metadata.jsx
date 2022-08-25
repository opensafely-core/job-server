import React from "react";
import prettyFileSize from "../../utils/pretty-file-size";
import { selectedFileProps } from "../../utils/props";

function Metadata({ fileDate, fileName, fileSize, fileUrl, metadata }) {
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

  const derp = Object.keys(metadata).map((key) => (
    <div key={key} className="mt-3">
      <strong>{key}</strong>
      <div>{metadata[key]}</div>
    </div>
  ));

  return (
    <div className="card-header">
      <ul className="list-inline small text-monospace d-flex mb-0">
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
      <div>{derp}</div>
    </div>
  );
}

export default Metadata;

Metadata.propTypes = {
  fileDate: selectedFileProps.date.isRequired,
  fileName: selectedFileProps.name.isRequired,
  fileSize: selectedFileProps.size.isRequired,
  fileUrl: selectedFileProps.url.isRequired,
  metadata: selectedFileProps.metadata.isRequired,
};
