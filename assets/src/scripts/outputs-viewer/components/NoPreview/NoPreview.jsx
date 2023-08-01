import PropTypes from "prop-types";
import React from "react";
import { selectedFileProps } from "../../utils/props";
import Link from "../Link";

function NoPreview({ error, fileUrl }) {
  return (
    <>
      {error ? <p>Error: {error.message}</p> : null}
      <p className="mb-3">We cannot show a preview of this file.</p>
      <p>
        <Link href={fileUrl} newTab>
          Open file in a new tab &#8599;
        </Link>
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
