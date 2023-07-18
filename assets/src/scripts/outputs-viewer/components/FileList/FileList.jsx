import PropTypes from "prop-types";
import React, { createRef, useEffect, useRef, useState } from "react";
import { Card } from "react-bootstrap";
import { useNavigate, useLocation } from "react-router-dom";
import { FixedSizeList } from "react-window";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import prettyFileSize from "../../utils/pretty-file-size";
import { datasetProps } from "../../utils/props";
import Filter from "./Filter";

function FileList({
  authToken,
  filesUrl,
  listVisible,
  setListVisible,
  setSelectedFile,
}) {
  const [files, setFiles] = useState([]);
  const [listHeight, setListHeight] = useState(0);
  const [fileIndex, setFileIndex] = useState(null);

  const { data, isError, isLoading } = useFileList({ authToken, filesUrl });
  const navigate = useNavigate();
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
      (file) => `/${file.name}` === location.pathname,
    );

    if (files[selectedItem]) {
      setFileIndex(selectedItem);
      setSelectedFile(files[selectedItem]);
    }
  }, [data, files, location, setSelectedFile]);

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

    navigate(itemName);
    return setSelectedFile(item);
  };

  return (
    <div className={`sidebar ${listVisible ? "d-block" : "d-none"}`}>
      <Filter files={data} listRef={listRef} setFiles={setFiles} />{" "}
      <Card className="pt-2">
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
                <span>{files[index].name}</span>
              ) : (
                <a
                  className="list-item__link"
                  disabled={`/${files[index].name}` === location.pathname}
                  href={files[index].url}
                  onClick={(e) => selectFile({ e, item: files[index] })}
                  title={`File size: ${prettyFileSize(files[index].size)}`}
                >
                  {files[index].name}
                </a>
              )}
            </li>
          )}
        </FixedSizeList>
      </Card>
    </div>
  );
}

export default FileList;

FileList.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  filesUrl: datasetProps.filesUrl.isRequired,
  listVisible: PropTypes.bool.isRequired,
  setListVisible: PropTypes.func.isRequired,
  setSelectedFile: PropTypes.func.isRequired,
};
