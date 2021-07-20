import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import { useQuery } from "react-query";
import useWindowSize from "../../hooks/useWindowSize";
import handleErrors from "../../utils/fetch-handle-errors";
import classes from "./FileList.module.scss";

function ListWrapper({ appHeight, children, listVisible }) {
  return (
    <ul
      className={`${classes.list} list-unstyled card ${
        listVisible ? "d-block" : "d-none"
      }`}
      style={{ height: appHeight || "auto" }}
    >
      {children}
    </ul>
  );
}

function FileList({ apiUrl, listVisible, setFile, setListVisible }) {
  const windowSize = useWindowSize();
  const [appHeight, setAppHeight] = useState(0);

  const { isLoading, isError, data, error } = useQuery("FILE_LIST", async () =>
    fetch(apiUrl)
      .then(handleErrors)
      .then(async (response) => response.json())
  );

  useEffect(() => {
    if (window.innerWidth > 991) {
      setListVisible(true);
      setAppHeight(
        window.innerHeight -
          document.querySelector("#outputsSPA").getBoundingClientRect().top -
          30
      );
    }
  }, [windowSize, setListVisible, listVisible]);

  if (isLoading) {
    return (
      <ListWrapper appHeight={appHeight} listVisible={listVisible}>
        <li className={classes.item}>Loading…</li>
      </ListWrapper>
    );
  }

  if (isError) {
    // eslint-disable-next-line no-console
    console.error(error.message);

    return (
      <ListWrapper appHeight={appHeight} listVisible={listVisible}>
        <li className={classes.item}>Error: Unable to load files</li>
      </ListWrapper>
    );
  }

  const sortedFiles = [
    ...data.files.sort((a, b) => {
      const nameA = a.name.toUpperCase();
      const nameB = b.name.toUpperCase();

      if (nameA < nameB) return -1;
      if (nameA > nameB) return 1;
      return 0;
    }),
  ];

  return (
    <ListWrapper appHeight={appHeight} listVisible={listVisible}>
      {sortedFiles.map((item) => (
        <li key={item.url} className={classes.item}>
          <a
            href={item.url}
            onClick={(e) => {
              e.preventDefault();
              return setFile({
                date: item.date,
                name: item.name,
                url: item.url,
                size: item.size,
              });
            }}
          >
            {item.name}
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
  appHeight: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
  listVisible: PropTypes.bool.isRequired,
};
