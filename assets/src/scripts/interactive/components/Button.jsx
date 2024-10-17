import { bool, func, node, oneOf, string } from "prop-types";
import React from "react";
import { classNames } from "../utils";

function Button({
  children,
  className = "",
  disabled = false,
  onClick = () => null,
  size = "md",
  type = "button",
  variant = "primary",
}) {
  return (
    <button
      className={classNames(
        "inline-flex w-fit items-center justify-center rounded border-b-2 shadow transition-buttons duration-200 px-4 py-2 font-semibold",
        "hover:shadow-lg",
        "focus:ring-offset-white focus:outline-none focus:ring-2 focus:ring-offset-2",
        variant === "primary"
          ? "bg-oxford-600 border-b-oxford-700 text-white hover:bg-oxford-700 focus:bg-oxford-700 focus:ring-oxford-500"
          : null,
        variant === "danger"
          ? "bg-bn-ribbon-600 border-b-bn-ribbon-700 text-white hover:bg-bn-ribbon-700 focus:bg-bn-ribbon-700 focus:ring-bn-ribbon-500"
          : null,
        variant === "danger-outline"
          ? "bg-bn-ribbon-50 border border-bn-ribbon-200 border-b-bn-ribbon-200 text-bn-ribbon-700 hover:bg-bn-ribbon-100 focus:bg-bn-ribbon-100 focus:ring-bn-ribbon-400"
          : null,
        size === "sm" ? "text-sm !px-2 !py-1.5 font-normal" : null,
        disabled
          ? "opacity-75 cursor-not-allowed !bg-gray-700 !border-b-gray-800"
          : null,
        className,
      )}
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
  children: node.isRequired,
  className: string,
  disabled: bool,
  onClick: func,
  size: oneOf(["sm", "md", "lg"]),
  type: oneOf(["button", "submit", "reset"]),
  variant: oneOf(["primary", "danger", "danger-outline"]),
};
