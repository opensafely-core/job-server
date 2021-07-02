import React from "react";
import { useQuery } from "react-query";
import classes from "./FileList.module.scss";

const dummyData = [
  "src/file1.html",
  "src/file2.svg",
  "src/file3.csv",
  "src/file4.png",
  "src/file5.txt",
];

function FileList() {
  const { isLoading, isError, data, error } = useQuery(
    "FILE_LIST",
    () => fetch("/"),
    {
      initialData: dummyData,
      staleTime: Infinity,
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
      {data.map((item) => (
        <li key={item} className={classes.item}>
          {item}
        </li>
      ))}
    </ul>
  );
}

export default FileList;
