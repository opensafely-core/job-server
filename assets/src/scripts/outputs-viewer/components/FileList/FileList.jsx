import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import { useQuery } from "react-query";
import useWindowSize from "../../hooks/useWindowSize";
import handleErrors from "../../utils/fetch-handle-errors";
import classes from "./FileList.module.scss";

function FileList({ apiUrl, setFile }) {
  const windowSize = useWindowSize();
  const [appHeight, setAppHeight] = useState("");

  const { isLoading, isError, data, error } = useQuery("FILE_LIST", async () =>
    fetch(apiUrl)
      .then(handleErrors)
      .then(async (response) => response.json())
  );

  useEffect(() => {
    setAppHeight(
      window.innerHeight -
        document.querySelector("#outputsSPA").getBoundingClientRect().top -
        30
    );
  }, [windowSize]);

  if (isLoading) {
    return (
      <ul
        className={`${classes.list} list-unstyled card`}
        style={{ height: appHeight }}
      >
        <li className={classes.item}>Loading…</li>
      </ul>
    );
  }

  if (isError) {
    // eslint-disable-next-line no-console
    console.error(error.message);

    return (
      <ul
        className={`${classes.list} list-unstyled card`}
        style={{ height: appHeight }}
      >
        <li className={classes.item}>Error: Unable to load file</li>
      </ul>
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
    <ul
      className={`${classes.list} list-unstyled card`}
      style={{ height: appHeight }}
    >
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
    </ul>
  );
}

export default FileList;

FileList.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  setFile: PropTypes.func.isRequired,
};
