import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import prettyFileSize from "../../utils/pretty-file-size";

function Metadata({ date, name, size, url }) {
  const fileSize = prettyFileSize(size);
  const [isValidDate, setIsValidDate] = useState();

  useEffect(() => {
    if (date !== "") {
      setIsValidDate(true);
    }
  }, [date]);

  let getDate;
  let fileDateAbs;
  let fileDate;

  if (isValidDate) {
    getDate = new Date(date);
    fileDateAbs = getDate.toISOString();
    fileDate = new Intl.DateTimeFormat("en-GB", {
      timeZone: "UTC",
      dateStyle: "short",
      timeStyle: "short",
    }).format(getDate);
  }

  return (
    <ul className="list-inline small text-monospace d-flex mb-0">
      <li className="list-inline-item">
        <a
          className="file-link d-flex"
          href={url}
          rel="noreferrer noopener"
          target="filePreview"
        >
          {name}
        </a>
      </li>
      {isValidDate && (
        <li className="list-inline-item ml-auto">
          <div className="sr-only">Last modified at: </div>
          <time
            className="file-date"
            dateTime={fileDateAbs}
            title={fileDateAbs}
          >
            {fileDate}
          </time>
        </li>
      )}
      <li className="list-inline-item spacer">{fileSize}</li>
    </ul>
  );
}

export default Metadata;

Metadata.propTypes = {
  date: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  size: PropTypes.number.isRequired,
  url: PropTypes.string.isRequired,
};
