import PropTypes from "prop-types";
import React from "react";

function Image({ data }) {
  return <img alt="" className="img" src={data} />;
}

export default Image;

Image.propTypes = {
  data: PropTypes.string.isRequired,
};
