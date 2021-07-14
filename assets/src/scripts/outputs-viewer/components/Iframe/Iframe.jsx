import PropTypes from "prop-types";
import React from "react";

function Iframe({ fileUrl, data }) {
  return (
    <iframe
      frameBorder="0"
      src={fileUrl}
      srcDoc={data}
      title={fileUrl}
      width="100%"
    />
  );
}

Iframe.propTypes = {
  data: PropTypes.string.isRequired,
  fileUrl: PropTypes.string.isRequired,
};

export default Iframe;
