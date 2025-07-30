import PropTypes from "prop-types";
import React, { useLayoutEffect, useState } from "react";
import useWindowSize from "../../hooks/use-window-size";
import { selectedFileProps } from "../../utils/props";

function Iframe({ data, fileName, fileUrl }) {
  const windowSize = useWindowSize();
  const [frameHeight, setFrameHeight] = useState(0);
  const id = encodeURIComponent(fileUrl).replace(/\W/g, "");

  // biome-ignore lint/correctness/useExhaustiveDependencies: ESLint to Biome legacy ignore
  useLayoutEffect(() => {
    // On screens wider than 991px, we will set a height
    // 991px is used as this is the size of the breakpoint in the sidebar CSS
    if (window.innerWidth > 991) {
      // If the iframe is offsetHeight is smaller than 1000 pixels, set it to 1000px
      // This is a magic number of roughly a good height for most screens viewing content
      if (document.getElementById(id).offsetHeight < 1000)
        return setFrameHeight(1000);
      // Otherwise, set the height to be the height of the #outputsSPA element
      return setFrameHeight(document.getElementById("outputsSPA").offsetHeight);
    }
    // Otherwise, on small screens we will set the height to be the full height of the iframe content
    return setFrameHeight(1000);
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
