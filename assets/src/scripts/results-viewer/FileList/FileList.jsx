import axios from "axios";
import React from "react";
import { useQuery } from "react-query";
import classes from "./FileList.module.scss";

function FileList({ apiUrl }) {
  const { isLoading, isError, data, error } = useQuery(
    "FILE_LIST",
    async () => {
      const { data } = await axios.get(apiUrl);
      return data;
    }
  );

  if (isLoading) {
    return <span>Loading...</span>;
  }

  if (isError) {
    return <span>Error: {error.message}</span>;
  }

  return (
    <ul>
      {data.files.map((item) => (
        <li key={item.url} className={classes.item}>
          <a href={item.url}>{item.name}</a>
        </li>
      ))}
    </ul>
  );
}

export default FileList;
