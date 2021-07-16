import PropTypes from "prop-types";
import React from "react";
import classes from "./Iframe.module.scss";

function Iframe({ fileUrl, data }) {
  return (
    <iframe
      className={classes.iframe}
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
