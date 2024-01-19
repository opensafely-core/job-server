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
  const [fileSort, setFileSort] = useState("nameOrder");

  const { data, isError, isLoading, isSuccess } = useFileList({
    authToken,
    filesUrl,
  });
  const navigate = useNavigate();
  const location = useLocation();

  const listRef = createRef();

  useEffect(() => {
    const selectedItem = data?.find(
      (file) => `/${file.name}` === location.pathname,
    );

    setSelectedFile(selectedItem);

    if (data) {
      setFiles(data);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSuccess]);

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
    <div className={listVisible ? "block md:sticky md:top-2" : "hidden"}>
      <div className="flex flex-row items-center gap-2 mb-1">
        <label
          className="inline-block font-semibold text-sm text-slate-900 cursor-pointer flex-shrink-0"
          htmlFor="fileSort"
        >
          Sort files by
        </label>
        <select
          className="
            block w-full border-slate-300 text-slate-900 shadow-sm
            focus:border-oxford-500 focus:ring-oxford-500
            sm:text-sm
          "
          id="fileSort"
          name="file-sort"
          onChange={(e) => setFileSort(e.target.value)}
          value={fileSort}
        >
          <option value="nameOrder">File name</option>
          <option value="dateOrder">Created date</option>
        </select>
      </div>
      <Filter files={data} listRef={listRef} setFiles={setFiles} />
      <Card
        className="py-2 md:max-h-screen md:h-full overflow-x-auto md:overflow-y-auto"
        container={false}
      >
        <ul className="text-sm text-oxford-600 flex flex-col gap-y-1 items-start">
          {files
            .sort((a, b) => a[fileSort] - b[fileSort])
            .map((file) => (
              <React.Fragment key={file.id}>
                {file.visible && (
                  <li
                    className={`leading-tight px-4 ${
                      `/${file.name}` === location.pathname
                        ? "font-bold text-oxford-800"
                        : ""
                    }`}
                  >
                    {`/${file.name}` === location.pathname ? (
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
                )}
              </React.Fragment>
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
