import PropTypes from "prop-types";
import React from "react";

function Link({ children = null, className = null, href, newTab = false }) {
  return (
    <a
      className={`
        font-semibold text-oxford-600 underline underline-offset-2 decoration-oxford-300 transition-colors duration-200
        hover:decoration-transparent hover:text-oxford
        focus:decoration-transparent focus:text-oxford focus:bg-bn-sun-300
        ${className}
      `}
      href={href}
      rel={newTab ? "noreferrer noopener" : undefined}
      target={newTab ? "filePreview" : undefined}
    >
      {children}
    </a>
  );
}

export default Link;

Link.propTypes = {
  children: PropTypes.oneOfType([PropTypes.element, PropTypes.string]),
  className: PropTypes.string,
  href: PropTypes.string.isRequired,
  newTab: PropTypes.bool,
};
