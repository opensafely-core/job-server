import PropTypes from "prop-types";
import React from "react";
import classes from "./Image.module.scss";

function Image({ data }) {
  return <img alt="" className={classes.img} src={data} />;
}

export default Image;

Text.propTypes = {
  data: PropTypes.string.isRequired,
};
