import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import classes from "./FileList.module.scss";

function ListWrapper({ listHeight, children, listVisible }) {
  return (
    <ul
      className={`${classes.list} list-unstyled card ${
        listVisible ? "d-block" : "d-none"
      }`}
      style={{ height: listHeight || "auto" }}
    >
      {children}
    </ul>
  );
}

function FileList({ apiUrl, listVisible, setFile, setListVisible }) {
  const windowSize = useWindowSize();
  const [listHeight, setListHeight] = useState(0);

  const { isLoading, isError, data, error } = useFileList({ apiUrl });

  useEffect(() => {
    if (window.innerWidth > 991) {
      setListVisible(true);
      setListHeight(
        window.innerHeight -
          document.querySelector("#outputsSPA").getBoundingClientRect().top -
          30
      );
    } else {
      setListHeight(0);
    }
  }, [windowSize, setListVisible, listVisible]);

  if (isLoading) {
    return (
      <ListWrapper listHeight={listHeight} listVisible={listVisible}>
        <li className={classes.item}>Loading…</li>
      </ListWrapper>
    );
  }

  if (isError) {
    // eslint-disable-next-line no-console
    console.error(error.message);

    return (
      <ListWrapper listHeight={listHeight} listVisible={listVisible}>
        <li className={classes.item}>Error: Unable to load files</li>
      </ListWrapper>
    );
  }

  return (
    <ListWrapper listHeight={listHeight} listVisible={listVisible}>
      {data.map((item) => (
        <li key={item.url} className={classes.item}>
          <a
            href={item.url}
            onClick={(e) => {
              e.preventDefault();
              return setFile({ ...item });
            }}
          >
            {item.shortName}
          </a>
        </li>
      ))}
    </ListWrapper>
  );
}

export default FileList;

FileList.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  listVisible: PropTypes.bool.isRequired,
  setFile: PropTypes.func.isRequired,
  setListVisible: PropTypes.func.isRequired,
};

ListWrapper.propTypes = {
  listHeight: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
  listVisible: PropTypes.bool.isRequired,
};
