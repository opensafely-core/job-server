import PropTypes from "prop-types";
import React, { createRef, useState } from "react";
import { Card, FormCheck, ListGroup } from "react-bootstrap";
import { Link, useLocation } from "react-router-dom";
import useFileList from "../../hooks/use-file-list";
import useFileStore from "../../stores/use-file-store";
import Filter from "./Filter";

function FileList({ isReviewEdit, listVisible, setSelectedFile }) {
  const [files, setFiles] = useState([]);
  const listRef = createRef();
  const location = useLocation();
  const { isFileChecked } = useFileStore((state) => ({
    isFileChecked: state.isFileChecked,
    checkedFiles: state.checkedFiles, // Update when checkedFiles changes
  }));

  const { data, isError, isLoading } = useFileList({
    setSelectedFile,
  });

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
                  checked={isFileChecked(file)}
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
  isReviewEdit: PropTypes.bool,
  listVisible: PropTypes.bool.isRequired,
  setSelectedFile: PropTypes.func.isRequired,
};

FileList.defaultProps = {
  isReviewEdit: false,
};
