import PropTypes from "prop-types";
import React, { useLayoutEffect, useState } from "react";
import useWindowSize from "../../hooks/use-window-size";
import { selectedFileProps } from "../../utils/props";

function Iframe({ data, selectedFile: { name, url } }) {
  const windowSize = useWindowSize();
  const [frameHeight, setFrameHeight] = useState(0);
  const id = encodeURIComponent(url).replace(/\W/g, "");

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
      src={url}
      srcDoc={data}
      title={name}
      width="100%"
    />
  );
}

export default Iframe;

Iframe.propTypes = {
  data: PropTypes.string.isRequired,
  selectedFile: PropTypes.shape({
    name: selectedFileProps.name.isRequired,
    url: selectedFileProps.name.isRequired,
  }).isRequired,
};
