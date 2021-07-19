import prettyBytes from "pretty-bytes";
import PropTypes from "prop-types";
import React from "react";
import dateFmt from "../../utils/date-format";
import classes from "./Metadata.module.scss";

function Metadata({ file }) {
  const fileSize = prettyBytes(file.size, { locale: "en-gb" });
  const fileDate = dateFmt({
    date: file.date,
    output: "yyyy-MM-dd HH:mm",
  });
  const fileDateAbs = dateFmt({
    date: file.date,
    output: "yyyy-MM-dd'T'HH:mm:ssXX",
  });

  return (
    <ul className="list-inline small text-monospace d-flex mb-0">
      <li className="list-inline-item">
        <a
          className={classes.fileLink}
          href={file.url}
          rel="noreferrer noopener"
          target="filePreview"
        >
          {file.name}
        </a>
      </li>
      <li className="list-inline-item ml-auto">
        <div className="sr-only">Last modified at: </div>
        <time dateTime={fileDateAbs} title={fileDateAbs}>
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
