import PropTypes from "prop-types";
import React from "react";
import classes from "./Image.module.scss";

function Image({ fileUrl }) {
  return <img alt="" className={classes.img} src={fileUrl} />;
}

Image.propTypes = {
  fileUrl: PropTypes.string.isRequired,
};

export default Image;
