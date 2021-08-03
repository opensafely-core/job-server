import PropTypes from "prop-types";
import React from "react";
import useFileList from "../../hooks/use-file-list";

function List({ apiUrl, authToken, setFile }) {
  const { data, error, isError, isLoading } = useFileList({
    apiUrl,
    authToken,
  });

  if (isLoading) {
    return <li>Loading…</li>;
  }

  if (isError) {
    // eslint-disable-next-line no-console
    console.error(error.message);

    return <li>Error: Unable to load files</li>;
  }

  const selectFile = ({ e, item }) => {
    e.preventDefault();
    return setFile({ ...item });
  };

  return (
    <>
      {data.map((item) => (
        <li key={item.url}>
          <a href={item.url} onClick={(e) => selectFile({ e, item })}>
            {item.shortName}
          </a>
        </li>
      ))}
    </>
  );
}

export default List;

List.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  authToken: PropTypes.string,
  setFile: PropTypes.func.isRequired,
};

List.defaultProps = {
  authToken: null,
};
