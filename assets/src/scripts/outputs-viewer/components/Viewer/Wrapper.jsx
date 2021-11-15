import PropTypes from "prop-types";
import React from "react";
import { useFiles } from "../../context/FilesProvider";
import Metadata from "../Metadata/Metadata";

function Wrapper({ children }) {
  const {
    state: { file },
  } = useFiles();

  return (
    <div className="card">
      <div className="card-header">
        <Metadata file={file} />
      </div>
      <div className="card-body">{children}</div>
    </div>
  );
}

export default Wrapper;

Wrapper.propTypes = {
  children: PropTypes.node.isRequired,
};
