import PropTypes from "prop-types";
import React from "react";
import classes from "./Wrapper.module.scss";

function Wrapper({ listHeight, children, listVisible }) {
  return (
    <ul
      className={`${classes.list} list-unstyled card ${
        listVisible ? "d-block" : "d-none"
      }`}
      style={{ height: listHeight || "auto" }}
    >
      {children}
    </ul>
  );
}

Wrapper.propTypes = {
  listHeight: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
  listVisible: PropTypes.bool.isRequired,
};

export default Wrapper;
