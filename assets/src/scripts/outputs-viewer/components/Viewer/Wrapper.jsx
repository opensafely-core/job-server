import PropTypes from "prop-types";
import React from "react";
import useStore from "../../stores/use-store";
import Metadata from "../Metadata/Metadata";

function Wrapper({ children }) {
  const { file } = useStore();

  return (
    <>
      <div className="card">
        <div className="card-header">
          <Metadata file={file} />
        </div>
        <div className="card-body">{children}</div>
      </div>
    </>
  );
}

export default Wrapper;

Wrapper.propTypes = {
  children: PropTypes.node.isRequired,
};
