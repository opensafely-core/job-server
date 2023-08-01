import PropTypes from "prop-types";
import React, { createRef, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import useFileList from "../../hooks/use-file-list";
import prettyFileSize from "../../utils/pretty-file-size";
import { datasetProps } from "../../utils/props";
import Card from "../Card";
import Filter from "./Filter";

function FileList({ authToken, filesUrl, listVisible, setSelectedFile }) {
  const [files, setFiles] = useState([]);
  const [fileIndex, setFileIndex] = useState(null);

  const { data, isError, isLoading } = useFileList({ authToken, filesUrl });
  const navigate = useNavigate();
  const location = useLocation();

  const listRef = createRef();

  useEffect(() => {
    const selectedItem = files.findIndex(
      (file) => `/${file.name}` === location.pathname,
    );

    if (files[selectedItem]) {
      setFileIndex(selectedItem);
      setSelectedFile(files[selectedItem]);
    }
  }, [data, files, location, setSelectedFile]);

  if (isLoading) {
    return (
      <Card container>
        <p>Loading…</p>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card container header={<h2 className="font-semibold text-lg">Error</h2>}>
        <p>Unable to load files</p>
      </Card>
    );
  }

  const selectFile = ({ e, item }) => {
    e.preventDefault();

    const itemName = `/${item.name}`;

    // Don't push a state change if clicking on a new file
    if (
      itemName === location.pathname ||
      itemName === location?.location?.pathname
    ) {
      return null;
    }

    navigate(itemName);
    return setSelectedFile(item);
  };

  return (
    <div className={listVisible ? "block sticky top-2" : "hidden"}>
      <Filter files={data} listRef={listRef} setFiles={setFiles} />
      <Card
        className="py-2 px-4 max-h-screen h-full overflow-auto"
        container={false}
      >
        <ul className="text-sm text-oxford-600">
          {files.map((file, index) => (
            <li
              key={file.name}
              className={`h-6 leading-tight grid items-center ${
                fileIndex === index ? "font-bold text-oxford-800" : ""
              }`}
            >
              {fileIndex === index ? (
                <span>{file.shortName}</span>
              ) : (
                <a
                  disabled={`/${file.name}` === location.pathname}
                  href={file.url}
                  onClick={(e) => selectFile({ e, item: file })}
                  title={`File size: ${prettyFileSize(file.size)}`}
                >
                  {file.shortName}
                </a>
              )}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

export default FileList;

FileList.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  filesUrl: datasetProps.filesUrl.isRequired,
  listVisible: PropTypes.bool.isRequired,
  setSelectedFile: PropTypes.func.isRequired,
};
