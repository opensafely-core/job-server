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

  const { error, isError, isLoading } = useFileList();
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

    // Viewport size, minus the list height, minus 30px for spacing
    // If there are horizontal scrollbars, minus 17px for the scrollbar
    const fileListHeight =
      window.innerHeight -
      (listEl.current?.getBoundingClientRect().top || 0) -
      30 -
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
      <div className={`${classes.list} card`}>
        <ul>
          <li>Loading…</li>
        </ul>
      </div>
    );
  }

  if (isError) {
    // eslint-disable-next-line no-console
    console.error(error.message);

    return (
      <div className={`${classes.list} card`}>
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
    <div className={classes.sidebar}>
      <Filter
        className={`${listVisible ? "d-block" : "d-none"}`}
        listRef={listRef}
        setFiles={setFiles}
      />
      <FixedSizeList
        ref={listRef}
        className={`${classes.list} card ${listVisible ? "d-block" : "d-none"}`}
        height={listHeight}
        innerElementType="ul"
        itemCount={files.length}
        itemSize={21}
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
  );
}

export default FileList;
