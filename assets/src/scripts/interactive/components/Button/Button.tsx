/* eslint-disable react/button-has-type */
import React from "react";
import { classNames } from "../../utils";

interface ButtonProps {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  size?: "sm" | "md" | "lg";
  type?: React.ButtonHTMLAttributes<HTMLButtonElement>["type"];
  variant?: "primary" | "danger";
}

function Button({
  children,
  className,
  disabled,
  onClick,
  size,
  type,
  variant,
}: ButtonProps) {
  return (
    <button
      className={classNames(
        "inline-flex w-fit items-center justify-center rounded border-b-2 border-b-current shadow transition-buttons duration-200 px-4 py-2 font-semibold",
        "hover:shadow-lg",
        "focus:ring-offset-white focus:outline-none focus:ring-2 focus:ring-offset-2",
        variant === "primary"
          ? "bg-oxford-600 border-b-oxford-700 text-white hover:bg-oxford-700 focus:bg-oxford-700 focus:ring-oxford-500"
          : null,
        variant === "danger"
          ? "bg-bn-ribbon-600 border-b-bn-ribbon-700 text-white hover:bg-bn-ribbon-700 focus:bg-bn-ribbon-700 focus:ring-bn-ribbon-500"
          : null,
        size === "sm" ? "text-sm px-3 py-2 font-normal" : null,
        disabled
          ? "opacity-75 cursor-not-allowed !bg-gray-700 !border-b-gray-800"
          : null,
        className
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

Button.defaultProps = {
  className: "",
  disabled: false,
  onClick: () => null,
  size: "md",
  type: "button",
  variant: "primary",
} as Partial<ButtonProps>;
