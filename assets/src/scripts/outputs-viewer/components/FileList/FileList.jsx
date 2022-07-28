import PropTypes from "prop-types";
import React, { createRef, useEffect, useRef, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { FixedSizeList } from "react-window";
import { useFiles } from "../../context/FilesProvider";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import prettyFileSize from "../../utils/pretty-file-size";
import Filter from "./Filter";

function FileList({ listVisible, setListVisible }) {
  const [files, setFiles] = useState([]);
  const [listHeight, setListHeight] = useState(0);
  const [fileIndex, setFileIndex] = useState(null);

  const { dispatch } = useFiles();
  const { data, isError, isLoading } = useFileList();
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
      // If the viewport height is taller than 600px
      // Use the viewport height
      // Otherwise use 600px
      (window.innerHeight > 600 ? window.innerHeight : 600) -
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
      setListVisible(true);
      return setListHeight(fileListHeight);
    }

    return setListHeight(fileListHeight);
  }, [files, listVisible, setListVisible, windowSize]);

  useEffect(() => {
    const selectedItem = files.findIndex(
      (file) => `/${file.name}` === location.pathname
    );

    if (files[selectedItem]) {
      setFileIndex(selectedItem);
      dispatch({ type: "update", state: { file: { ...files[selectedItem] } } });
    }
  }, [dispatch, data, files, location]);

  if (isLoading) {
    return (
      <div className="list card p-2">
        <ul>
          <li>Loading…</li>
        </ul>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="list card p-2">
        <ul>
          <li>Error: Unable to load files</li>
        </ul>
      </div>
    );
  }

  const selectFile = ({ e, item }) => {
    e.preventDefault();

    const itemName = `/${item.name}`;

    // Don't push a state change if clicking on a new file
    if (
      itemName === location.pathname ||
      itemName === location?.location?.pathname
    ) {
      return null;
    }

    history.push(itemName);
    return dispatch({ type: "update", state: { file: { ...item } } });
  };

  return (
    <div className={`sidebar ${listVisible ? "d-block" : "d-none"}`}>
      <Filter files={data} listRef={listRef} setFiles={setFiles} />{" "}
      <div className="card pt-2">
        <FixedSizeList
          ref={listRef}
          className="list"
          height={listHeight}
          innerElementType="ul"
          itemCount={files.length}
          itemSize={25}
          outerRef={listEl}
          width="100%"
        >
          {({ index, style }) => (
            <li
              className={`list-item ${
                fileIndex === index && "list-item--selected"
              }`}
              style={style}
            >
              {fileIndex === index ? (
                <span>{files[index].shortName}</span>
              ) : (
                <a
                  className="list-item__link"
                  disabled={`/${files[index].name}` === location.pathname}
                  href={files[index].url}
                  onClick={(e) => selectFile({ e, item: files[index] })}
                  title={`File size: ${prettyFileSize(files[index].size)}`}
                >
                  {files[index].shortName}
                </a>
              )}
            </li>
          )}
        </FixedSizeList>
      </div>
    </div>
  );
}

export default FileList;

FileList.propTypes = {
  listVisible: PropTypes.bool.isRequired,
  setListVisible: PropTypes.func.isRequired,
};
