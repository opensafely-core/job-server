import React, { useEffect, useRef, useState } from "react";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import useStore from "../../stores/use-store";
import List from "./List";
import Wrapper from "./Wrapper";

function FileList() {
  const { listVisible } = useStore();
  const [listHeight, setListHeight] = useState(0);
  const listEl = useRef(null);
  const windowSize = useWindowSize();

  const { data } = useFileList();

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
      useStore.setState({ listVisible: true });
      return setListHeight(fileListHeight);
    }

    return setListHeight(0);
  }, [data, listVisible, windowSize]);

  return (
    <Wrapper ref={listEl} listHeight={listHeight}>
      <List />
    </Wrapper>
  );
}

export default FileList;
