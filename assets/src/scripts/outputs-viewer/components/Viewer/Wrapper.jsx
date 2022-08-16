import PropTypes from "prop-types";
import React from "react";
import Metadata from "../Metadata/Metadata";

function Wrapper({ children, selectedFile }) {
  return (
    <div className="card">
      <div className="card-header">
        <Metadata {...selectedFile} />
      </div>
      <div className="card-body">{children}</div>
    </div>
  );
}

export default Wrapper;

Wrapper.propTypes = {
  children: PropTypes.node.isRequired,
};
