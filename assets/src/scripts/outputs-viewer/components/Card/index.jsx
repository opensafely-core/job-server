import PropTypes from "prop-types";
import React from "react";

function Card({ className, container, header, innerClassName, children }) {
  return (
    <div className={`bg-white shadow ${className}`}>
      {header ? (
        <div className="flex flex-wrap gap-2 items-center justify-between px-4 py-2 sm:px-6 sm:py-4 sm:flex-nowrap bg-slate-50">
          {header}
        </div>
      ) : null}
      <div
        className={`
          ${innerClassName}
          ${container ? "px-4 py-3 md:px-6 md:py-5" : ""}
          ${header && container ? "border-t border-slate-200" : ""}
        `}
      >
        {children}
      </div>
    </div>
  );
}

export default Card;

Card.propTypes = {
  children: PropTypes.element.isRequired,
  className: PropTypes.string,
  container: PropTypes.bool,
  header: PropTypes.element,
  innerClassName: PropTypes.string,
};

Card.defaultProps = {
  className: "",
  container: false,
  header: null,
  innerClassName: "",
};
