import PropTypes from "prop-types";
import React from "react";

function NoPreview({ error, selectedFile }) {
  return (
    <>
      {error ? <p>Error: {error.message}</p> : null}
      <p>We cannot show a preview of this file.</p>
      <p className="mb-0">
        <a href={selectedFile.url} rel="noreferrer noopener" target="_blank">
          Open file in a new tab &#8599;
        </a>
      </p>
    </>
  );
}

export default NoPreview;

NoPreview.propTypes = {
  error: PropTypes.shape({
    message: PropTypes.string,
  }),
};

NoPreview.defaultProps = {
  error: null,
};
