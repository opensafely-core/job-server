import axios from "axios";
import PropTypes from "prop-types";
import React from "react";
import { useQuery } from "react-query";
import classes from "./FileList.module.scss";

function FileList({ apiUrl, setFileUrl }) {
  const { isLoading, isError, data, error } = useQuery(
    "FILE_LIST",
    async () => {
      const { data: files } = await axios.get(apiUrl);
      return files;
    }
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

      if (nameA < nameB) {
        return -1;
      }

      if (nameA > nameB) {
        return 1;
      }

      return 0;
    }),
  ];

  return (
    <ul>
      {sortedFiles.map((item) => (
        <li key={item.url} className={classes.item}>
          <a
            href={item.url}
            onClick={(e) => {
              e.preventDefault();
              return setFileUrl(item.url);
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
  setFileUrl: PropTypes.func.isRequired,
};
