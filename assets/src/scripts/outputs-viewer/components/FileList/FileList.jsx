import PropTypes from "prop-types";
import React, { useEffect, useRef, useState } from "react";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import List from "./List";
import Wrapper from "./Wrapper";

function FileList({ apiUrl, listVisible, setFile, setListVisible }) {
  const [listHeight, setListHeight] = useState(0);
  const listEl = useRef(null);
  const windowSize = useWindowSize();

  const { data } = useFileList({ apiUrl });

  useEffect(() => {
    const largeViewport = window.innerWidth > 991;
    const hasScrollbarX =
      listEl.current?.base.clientWidth < listEl.current?.base.scrollWidth;

    // Viewport size, minus the Outputs SPA height, minus 30px for spacing
    // If there are horizontal scrollbars, minus 17px for the scrollbar
    const fileListHeight =
      window.innerHeight -
      document.querySelector("#outputsSPA").getBoundingClientRect().top -
      30 -
      (hasScrollbarX ? 17 : 0);

    if (largeViewport) {
      setListVisible(true);
      return setListHeight(fileListHeight);
    }

    return setListHeight(0);
  }, [windowSize, setListVisible, listVisible, data]);

  return (
    <Wrapper ref={listEl} listHeight={listHeight} listVisible={listVisible}>
      <List apiUrl={apiUrl} setFile={setFile} />
    </Wrapper>
  );
}

export default FileList;

FileList.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  listVisible: PropTypes.bool.isRequired,
  setFile: PropTypes.func.isRequired,
  setListVisible: PropTypes.func.isRequired,
};
