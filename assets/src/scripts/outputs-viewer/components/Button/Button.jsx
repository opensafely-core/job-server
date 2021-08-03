import PropTypes from "prop-types";
import React from "react";

function Button({ isLoading, onClickFn, text }) {
  function onClick(e) {
    e.preventDefault();
    return onClickFn();
  }

  return (
    <button
      className={`btn btn-${isLoading ? "secondary" : "primary"}`}
      disabled={isLoading}
      onClick={(e) => onClick(e)}
      type="button"
    >
      {isLoading ? text.loading : text.default}
    </button>
  );
}

Button.propTypes = {
  isLoading: PropTypes.bool.isRequired,
  onClickFn: PropTypes.func.isRequired,
  text: PropTypes.shape({
    default: PropTypes.string.isRequired,
    loading: PropTypes.string.isRequired,
  }).isRequired,
};

export default Button;
