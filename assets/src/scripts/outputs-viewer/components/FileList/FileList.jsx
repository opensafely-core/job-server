import React, { createRef, useEffect, useRef, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { FixedSizeList } from "react-window";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import useStore from "../../stores/use-store";
import prettyFileSize from "../../utils/pretty-file-size";
import classes from "./FileList.module.scss";
import Filter from "./Filter";

function FileList() {
  const [files, setFiles] = useState([]);
  const [listHeight, setListHeight] = useState(0);

  const { data, isError, isLoading } = useFileList();
  const { listVisible } = useStore();
  const history = useHistory();
  const location = useLocation();

  const windowSize = useWindowSize();

  const listEl = useRef(null);
  const listRef = createRef();

  useEffect(() => {
    const largeViewport = window.innerWidth > 991;
    const hasScrollbarX =
      listEl.current?.clientWidth < listEl.current?.scrollWidth;

    const fileListHeight =
      // Viewport size height
      window.innerHeight -
      // if the list exists
      // minus the height from the top of the list
      // else minus zero
      (listEl.current?.getBoundingClientRect().top || 0) -
      // minus 30px for spacing at the bottom
      30 -
      // if there are horizontal scrollbars
      // minus 17px for the scrollbar (magic number)
      (hasScrollbarX ? 17 : 0);

    if (largeViewport) {
      useStore.setState({ listVisible: true });
      return setListHeight(fileListHeight);
    }

    return setListHeight(fileListHeight);
  }, [files, windowSize]);

  useEffect(() => {
    const item = files.filter(
      (file) => `/${file.name}` === location.pathname
    )[0];

    if (item) {
      useStore.setState({ file: { ...item } });
    }
  }, [files, location]);

  if (isLoading) {
    return (
      <div className={`${classes.list} card p-2`}>
        <ul>
          <li>Loading…</li>
        </ul>
      </div>
    );
  }

  if (isError) {
    return (
      <div className={`${classes.list} card p-2`}>
        <ul>
          <li>Error: Unable to load files</li>
        </ul>
      </div>
    );
  }

  const selectFile = ({ e, item }) => {
    e.preventDefault();

    const itemName = `/${item.name}`;
    // Only push a state change if clicking on a new file
    if (itemName !== location.pathname) {
      history.push(itemName);
      return useStore.setState({ file: { ...item } });
    }

    return null;
  };

  return (
    <div className={`${classes.sidebar} ${listVisible ? "d-block" : "d-none"}`}>
      <Filter files={data} listRef={listRef} setFiles={setFiles} />{" "}
      <div className="card pt-2">
        <FixedSizeList
          ref={listRef}
          className={classes.list}
          height={listHeight}
          innerElementType="ul"
          itemCount={files.length}
          itemSize={25}
          outerRef={listEl}
          width="100%"
        >
          {({ index, style }) => (
            <li style={style}>
              <a
                href={files[index].url}
                onClick={(e) => selectFile({ e, item: files[index] })}
                title={`File size: ${prettyFileSize(files[index].size)}`}
              >
                {files[index].shortName}
              </a>
            </li>
          )}
        </FixedSizeList>
      </div>
    </div>
  );
}

export default FileList;
