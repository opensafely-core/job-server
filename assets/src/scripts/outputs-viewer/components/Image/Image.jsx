import PropTypes from "prop-types";
import React from "react";

function Image({ data }) {
  return <img alt="" className="h-auto max-w-full" src={data} />;
}

export default Image;

Image.propTypes = {
  data: PropTypes.string.isRequired,
};
