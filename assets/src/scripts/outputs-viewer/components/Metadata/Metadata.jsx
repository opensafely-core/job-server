import prettyBytes from "pretty-bytes";
import PropTypes from "prop-types";
import React from "react";
import dateFmt from "../../utils/date-format";

function Metadata({ file }) {
  const fileSize = prettyBytes(file.size, { locale: "en-gb" });
  const fileDate = dateFmt({ date: file.date });

  return (
    <div className="card bg-light mb-3">
      <div className="card-body">
        <h2 className="card-title h5 mb-0">{file.name}</h2>
      </div>
      <ul className="list-group list-group-flush">
        <li className="list-group-item">
          <strong>File size: </strong>
          {fileSize}
        </li>
        <li className="list-group-item">
          <strong>Last modified date: </strong>
          {fileDate}
        </li>
      </ul>
    </div>
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
