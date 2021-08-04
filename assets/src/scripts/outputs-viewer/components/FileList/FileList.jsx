import React, { useEffect, useRef, useState } from "react";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import useStore from "../../stores/use-store";
import Filter from "./Filter";
import List from "./List";

function FileList() {
  const { listVisible } = useStore();
  const [listHeight, setListHeight] = useState(0);
  const [files, setFiles] = useState([]);

  const listEl = useRef(null);
  const windowSize = useWindowSize();

  const { data } = useFileList();

  useEffect(() => {
    const largeViewport = window.innerWidth > 991;
    const hasScrollbarX =
      listEl.current?.clientWidth < listEl.current?.scrollWidth;

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
    <div
      ref={listEl}
      className={` card ${listVisible ? "d-block" : "d-none"}`}
      style={{ height: listHeight || "auto" }}
    >
      {data ? <Filter setFiles={setFiles} /> : null}
      <List files={files} />
    </div>
  );
}

export default FileList;
