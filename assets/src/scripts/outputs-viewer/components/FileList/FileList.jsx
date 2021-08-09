import React, { useEffect, useRef, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
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
  const { file, listVisible } = useStore();
  const history = useHistory();
  const location = useLocation();

  const windowSize = useWindowSize();

  const listEl = useRef(null);

  useEffect(() => {
    const largeViewport = window.innerWidth > 991;
    const hasScrollbarX =
      listEl.current?.clientWidth < listEl.current?.scrollWidth;

    // Viewport size, minus the list height, minus 30px for spacing
    // If there are horizontal scrollbars, minus 17px for the scrollbar
    const fileListHeight =
      window.innerHeight -
      listEl.current?.getBoundingClientRect().top -
      30 -
      (hasScrollbarX ? 17 : 0);

    if (largeViewport) {
      useStore.setState({ listVisible: true });
      return setListHeight(fileListHeight);
    }

    return setListHeight(0);
  }, [files, windowSize]);

  useEffect(() => {
    if (location.pathname !== file.name) {
      const item = files.filter((f) => `/${f.name}` === location.pathname)[0];
      if (item) {
        useStore.setState({ file: { ...item } });
      }
    }
  }, [file.name, files, location]);

  if (isLoading) {
    return (
      <ul className={`${classes.list} list-unstyled card`}>
        <li>Loading…</li>
      </ul>
    );
  }

  if (isError) {
    // eslint-disable-next-line no-console
    console.error(error.message);

    return (
      <ul className={`${classes.list} list-unstyled card`}>
        <li>Error: Unable to load files</li>
      </ul>
    );
  }

  const selectFile = ({ e, item }) => {
    e.preventDefault();
    history.push(item.name);
    return useStore.setState({ file: { ...item }, filePath: item.name });
  };

  return (
    <>
      <Filter setFiles={setFiles} />
      <ul
        ref={listEl}
        className={`${classes.list} list-unstyled card ${
          listVisible ? "d-block" : "d-none"
        }`}
        style={{ height: listHeight || "auto" }}
      >
        {files.map((item) => (
          <li key={item.url}>
            {!item.is_deleted && (
              <a
                href={item.url}
                onClick={(e) => selectFile({ e, item })}
                title={`File size: ${prettyFileSize(item.size)}`}
              >
                {item.shortName}
              </a>
            )}
            {item.is_deleted && <span>{item.shortName}</span>}
          </li>
        ))}
      </ul>
    </>
  );
}

export default FileList;
