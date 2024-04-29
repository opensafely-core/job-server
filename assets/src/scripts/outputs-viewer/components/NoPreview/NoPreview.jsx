import PropTypes from "prop-types";
import React from "react";
import { selectedFileProps } from "../../utils/props";
import Link from "../Link";

function NoPreview({ error = null, fileUrl }) {
  return (
    <>
      {error ? (
        <p>Error: Unable to load file</p>
      ) : (
        <p>We cannot show a preview of this file.</p>
      )}

      <p className="mt-3">
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
