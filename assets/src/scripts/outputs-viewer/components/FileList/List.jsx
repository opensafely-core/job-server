import PropTypes from "prop-types";
import React from "react";
import useFileList from "../../hooks/use-file-list";
import useStore from "../../stores/use-store";
import prettyFileSize from "../../utils/pretty-file-size";
import classes from "./List.module.scss";

function List({ files }) {
  const { error, isError, isLoading } = useFileList();

  if (isLoading) {
    return (
      <ul className={`${classes.list} list-unstyled`}>
        <li>Loading…</li>
      </ul>
    );
  }

  if (isError) {
    // eslint-disable-next-line no-console
    console.error(error.message);

    return (
      <ul className={`${classes.list} list-unstyled`}>
        <li>Error: Unable to load files</li>
      </ul>
    );
  }

  const selectFile = ({ e, item }) => {
    e.preventDefault();
    return useStore.setState({ file: { ...item } });
  };

  return (
    <ul className={`${classes.list} list-unstyled`}>
      {files.map((item) => (
        <li key={item.url}>
          <a
            href={item.url}
            onClick={(e) => selectFile({ e, item })}
            title={`File size: ${prettyFileSize(item.size)}`}
          >
            {item.shortName}
          </a>
        </li>
      ))}
    </ul>
  );
}

export default List;

List.propTypes = {
  files: PropTypes.arrayOf(PropTypes.shape).isRequired,
};
