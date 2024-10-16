import PropTypes from "prop-types";
import React from "react";

function Button({
  children,
  className = null,
  disabled = false,
  onClick = () => null,
  type = "button",
  variant = "primary",
}) {
  return (
    <button
      className={`
        inline-flex w-fit items-center justify-center rounded-md shadow-sm transition-buttons duration-200 px-4 py-2 text-sm font-medium

        ${
          !disabled
            ? `
              hover:shadow-lg
              focus:outline-none focus:ring-2 focus:ring-offset-2`
            : ""
        }

        ${
          variant === "primary"
            ? `
              bg-oxford-600 text-white
              hover:bg-oxford-700
              focus:bg-oxford-700 focus:ring-oxford-500 focus:ring-offset-white
            `
            : ``
        }
        ${
          variant === "secondary"
            ? `
              bg-slate-500 text-white
              hover:bg-slate-600
              focus:bg-slate-600 focus:ring-slate-500 focus:ring-offset-white
            `
            : ``
        }

        ${className}
      `}
      disabled={disabled}
      onClick={onClick}
      type={type}
    >
      {children}
    </button>
  );
}

export default Button;

Button.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  disabled: PropTypes.bool,
  onClick: PropTypes.func,
  type: PropTypes.string,
  variant: PropTypes.string,
};
