import PropTypes from "prop-types";
import React from "react";
import { useQuery } from "react-query";
import handleErrors from "../../utils/fetch-handle-errors";
import classes from "./FileList.module.scss";

function FileList({ apiUrl, setFile }) {
  const { isLoading, isError, data, error } = useQuery("FILE_LIST", async () =>
    fetch(apiUrl)
      .then(handleErrors)
      .then(async (response) => response.json())
  );

  if (isLoading) {
    return <span>Loading...</span>;
  }

  if (isError) {
    return <span>Error: {error.message}</span>;
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
    <ul className={`${classes.list} list-unstyled`}>
      {sortedFiles.map((item) => (
        <li key={item.url} className={classes.item}>
          <a
            href={item.url}
            onClick={(e) => {
              e.preventDefault();
              return setFile({ name: item.name, url: item.url });
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
