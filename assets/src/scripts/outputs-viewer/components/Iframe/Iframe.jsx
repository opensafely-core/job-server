import PropTypes from "prop-types";
import React, { useLayoutEffect, useState } from "react";
import useWindowSize from "../../hooks/use-window-size";
import { selectedFileProps } from "../../utils/props";

function Iframe({ data, fileName, fileUrl }) {
  const windowSize = useWindowSize();
  const [frameHeight, setFrameHeight] = useState(0);
  const id = encodeURIComponent(fileUrl).replace(/\W/g, "");

  useLayoutEffect(() => {
    const minHeight = 1000;
    if (document.getElementById(id) && window.innerWidth > 991) {
      const spaHeight = Math.round(
        document?.getElementById("outputsSPA")?.offsetHeight,
      );
      if (!spaHeight || spaHeight < minHeight) return setFrameHeight(minHeight);
    }
    return setFrameHeight(minHeight);
  }, [windowSize, id]);

  return (
    <iframe
      className="-mx-4 -my-3 w-[calc(100%+2rem)] md:-mx-6 md:-my-5 md:w-[calc(100%+3rem)]"
      frameBorder="0"
      height={frameHeight}
      id={id}
      src={fileUrl}
      srcDoc={data}
      title={fileName}
      width="100%"
    />
  );
}

export default Iframe;

Iframe.propTypes = {
  data: PropTypes.string.isRequired,
  fileName: selectedFileProps.name.isRequired,
  fileUrl: selectedFileProps.url.isRequired,
};
