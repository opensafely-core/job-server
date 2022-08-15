import PropTypes from "prop-types";
import React, { useLayoutEffect, useState } from "react";
import useWindowSize from "../../hooks/use-window-size";

function Iframe({ data, selectedFile }) {
  const windowSize = useWindowSize();
  const [frameHeight, setFrameHeight] = useState(0);
  const id = encodeURIComponent(selectedFile.url).replace(/\W/g, "");

  useLayoutEffect(() => {
    if (document.getElementById(id)) {
      if (window.innerWidth > 991) {
        setFrameHeight(
          Math.round(
            window.innerHeight -
              document.getElementById(id).getBoundingClientRect().top -
              17 - // Magic number for scroll bar height
              40 // 2rem
          )
        );
      } else {
        setFrameHeight(1000);
      }
    }
  }, [windowSize, id]);

  return (
    <iframe
      frameBorder="0"
      height={frameHeight}
      id={id}
      src={selectedFile.url}
      srcDoc={data}
      title={selectedFile.name}
      width="100%"
    />
  );
}

export default Iframe;

Iframe.propTypes = {
  data: PropTypes.string.isRequired,
};
