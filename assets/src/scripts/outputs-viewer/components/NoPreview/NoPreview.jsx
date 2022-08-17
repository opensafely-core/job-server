import PropTypes from "prop-types";
import React from "react";
import { selectedFileProps } from "../../utils/props";

function NoPreview({ error, fileUrl }) {
  return (
    <>
      {error ? <p>Error: {error.message}</p> : null}
      <p>We cannot show a preview of this file.</p>
      <p className="mb-0">
        <a href={fileUrl} rel="noreferrer noopener" target="_blank">
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
  fileUrl: selectedFileProps.url.isRequired,
};

NoPreview.defaultProps = {
  error: null,
};
