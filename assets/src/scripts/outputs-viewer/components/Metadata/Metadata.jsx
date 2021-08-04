import React from "react";
import useStore from "../../stores/use-store";
import prettyFileSize from "../../utils/pretty-file-size";
import classes from "./Metadata.module.scss";

function Metadata() {
  const { file } = useStore();

  const fileSize = prettyFileSize(file.size);
  const date = new Date(file.date);
  const fileDateAbs = date.toISOString();
  const fileDate = new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);

  return (
    <ul className="list-inline small text-monospace d-flex mb-0">
      <li className="list-inline-item">
        <a
          className={`${classes.fileLink} d-flex`}
          href={file.url}
          rel="noreferrer noopener"
          target="filePreview"
        >
          {file.name}
        </a>
      </li>
      <li className="list-inline-item ml-auto">
        <div className="sr-only">Last modified at: </div>
        <time
          className={classes.fileDate}
          dateTime={fileDateAbs}
          title={fileDateAbs}
        >
          {fileDate}
        </time>
      </li>
      <li className={`list-inline-item ${classes.spacer}`}>{fileSize}</li>
    </ul>
  );
}

export default Metadata;
