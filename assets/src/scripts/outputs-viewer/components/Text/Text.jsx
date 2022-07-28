import PropTypes from "prop-types";
import React from "react";

function Text({ data }) {
  return <pre className="txt">{data}</pre>;
}

export default Text;

Text.propTypes = {
  data: PropTypes.string.isRequired,
};
