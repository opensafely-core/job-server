import PropTypes from "prop-types";
import React from "react";

function Text({ data }) {
  return <pre className="whitespace-break-spaces break-words">{data}</pre>;
}

export default Text;

Text.propTypes = {
  data: PropTypes.string.isRequired,
};
