import PropTypes from "prop-types";
import React, { createRef, useEffect, useRef, useState } from "react";
import {
  Card,
  Form,
  FormCheck,
  ListGroup,
  ListGroupItem,
} from "react-bootstrap";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { FixedSizeList } from "react-window";
import useFileList from "../../hooks/use-file-list";
import useWindowSize from "../../hooks/use-window-size";
import prettyFileSize from "../../utils/pretty-file-size";
import { datasetProps } from "../../utils/props";
import Filter from "./Filter";

function FileList({
  authToken,
  checkedIds,
  filesUrl,
  isReviewEdit,
  listVisible,
  setSelectedFile,
  selectedFile,
}) {
  const { data, isError, isLoading, isSuccess } = useFileList({
    authToken,
    filesUrl,
  });
  const [files, setFiles] = useState([]);
  const listRef = createRef();
  const location = useLocation();

  useEffect(() => {
    if (isSuccess && !selectedFile) {
      setSelectedFile(
        data.find((file) => location.pathname.substring(1) === file.name)
      );
    }
  }, [data, isSuccess, location.pathname, setSelectedFile, selectedFile]);

  if (isLoading) {
    return (
      <div className="list card p-2">
        <ul>
          <li>Loading…</li>
        </ul>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="list card p-2">
        <ul>
          <li>Error: Unable to load files</li>
        </ul>
      </div>
    );
  }

  return (
    <div className={`sidebar ${listVisible ? "d-block" : "d-none"}`}>
      <Filter files={data} listRef={listRef} setFiles={setFiles} />{" "}
      <Card className="" style={{ maxHeight: "1000px", overflowY: "scroll" }}>
        <ListGroup variant="flush">
          {files.map((file) => (
            <ListGroup.Item
              key={file.id}
              action
              active={location.pathname.substring(1) === file.name}
              as={Link}
              onClick={() => setSelectedFile(file)}
              to={file.name}
            >
              {isReviewEdit ? (
                <FormCheck
                  checked={checkedIds.includes(file.id)}
                  label={file.shortName}
                  readOnly
                />
              ) : (
                file.shortName
              )}
            </ListGroup.Item>
          ))}
        </ListGroup>
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
