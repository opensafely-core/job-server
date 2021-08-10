import PropTypes from "prop-types";
import React from "react";
import classes from "./Image.module.scss";

function Image({ data }) {
  return <img alt="" className={classes.img} src={data} />;
}

export default Image;

Image.propTypes = {
  data: PropTypes.string.isRequired,
};
