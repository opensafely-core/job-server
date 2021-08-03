import PropTypes from "prop-types";
import React from "react";
import useStore from "../../stores/use-store";
import classes from "./Wrapper.module.scss";

function Wrapper({ listHeight, children }) {
  const { listVisible } = useStore();

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
  children: PropTypes.node.isRequired,
  listHeight: PropTypes.number.isRequired,
};

export default Wrapper;
