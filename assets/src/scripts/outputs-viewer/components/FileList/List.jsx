import React from "react";
import useFileList from "../../hooks/use-file-list";
import useStore from "../../stores/use-store";
import prettyFileSize from "../../utils/pretty-file-size";

function List() {
  const { data, error, isError, isLoading } = useFileList();

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
    return useStore.setState({ file: { ...item } });
  };

  return (
    <>
      {data.map((item) => (
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
    </>
  );
}

export default List;
