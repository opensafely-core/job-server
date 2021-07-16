import PropTypes from "prop-types";
import React from "react";

function Metadata({ file }) {
  return (
    <div className="card bg-light mb-3">
      <div className="card-body">
        <h2 className="card-title h5 mb-0">{file.name}</h2>
      </div>
      <ul className="list-group list-group-flush">
        <li className="list-group-item">
          <strong>File size: </strong>50 kb
        </li>
        <li className="list-group-item">
          <strong>Last modified date: </strong>
          01 Jan 2021
        </li>
      </ul>
    </div>
  );
}

Metadata.propTypes = {
  file: PropTypes.objectOf({
    name: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
  }).isRequired,
};

export default Metadata;
