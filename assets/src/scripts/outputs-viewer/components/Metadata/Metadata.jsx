import prettyBytes from "pretty-bytes";
import PropTypes from "prop-types";
import React from "react";
import classes from "./Metadata.module.scss";

function Metadata({ file }) {
  const fileSize = file.size
    ? prettyBytes(file.size, { locale: "en-gb" })
    : "unknown";
  const date = new Date(file.date);
  const fileDateAbs = date.toISOString();
  const fileDate = new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);

  return (
    <ul className="list-inline small text-monospace d-flex mb-0">
      <li className="list-inline-item">
        <a
          className={`${classes.fileLink} d-flex`}
          href={file.url}
          rel="noreferrer noopener"
          target="filePreview"
        >
          {file.name}
        </a>
      </li>
      <li className="list-inline-item ml-auto">
        <div className="sr-only">Last modified at: </div>
        <time
          className={classes.fileDate}
          dateTime={fileDateAbs}
          title={fileDateAbs}
        >
          {fileDate}
        </time>
      </li>
      <li className={`list-inline-item ${classes.spacer}`}>{fileSize}</li>
    </ul>
  );
}

Metadata.propTypes = {
  file: PropTypes.shape({
    date: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    size: PropTypes.number.isRequired,
    url: PropTypes.string.isRequired,
  }).isRequired,
};

export default Metadata;
