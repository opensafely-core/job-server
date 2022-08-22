import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React, { useState } from "react";
import { Button, Card, Col, Row } from "react-bootstrap";
// import { useLocation } from "react-router-dom";
import PrepareButton from "./components/Button/PrepareButton";
import PublishButton from "./components/Button/PublishButton";
import FileList from "./components/FileList/FileList";
import Metadata from "./components/Metadata/Metadata";
import Toast from "./components/Toast/Toast";
import Viewer from "./components/Viewer/Viewer";
import useReviewState from "./hooks/use-review-state";
import { datasetProps } from "./utils/props";

function App({
  authToken,
  csrfToken,
  filesUrl,
  prepareUrl,
  publishUrl,
  reviewUrl,
}) {
  const uuid = Date.now();
  const [listVisible, setListVisible] = useState(true);
  const [selectedFile, setSelectedFile] = useState();
  const [checkedIds, setCheckedIds] = useState([]);
  const { isReviewEdit, isReviewView, toggleReviewState, setReviewView } =
    useReviewState();

  const isReview = !!reviewUrl;

  return (
    <>
      {isReview && (
        <Row>
          <Col className="d-flex mb-3">
            <Button
              className="ml-auto"
              onClick={() => toggleReviewState()}
              variant="success"
            >
              {isReviewView
                ? "Prepare a review request"
                : "Submit review request"}
            </Button>
            {isReviewEdit ? (
              <Button
                className="ml-2"
                onClick={() => {
                  setReviewView();
                  setCheckedIds([]);
                }}
                variant="danger"
              >
                Cancel review request
              </Button>
            ) : null}
          </Col>
        </Row>
      )}
      {(prepareUrl || publishUrl) && !isReview ? (
        <Row className="mb-2">
          <Col>
            {prepareUrl && (
              <PrepareButton
                authToken={authToken}
                csrfToken={csrfToken}
                filesUrl={filesUrl}
                prepareUrl={prepareUrl}
              />
            )}
            {publishUrl && (
              <PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />
            )}
          </Col>
        </Row>
      ) : null}
      <Row className="mb-3">
        <Col lg={3}>
          <Button
            className="d-block d-lg-none mb-3"
            onClick={() => setListVisible(!listVisible)}
            type="button"
            variant="secondary"
          >
            {listVisible ? "Hide" : "Show"} file list
          </Button>
          {isReview && isReviewEdit ? (
            <Button
              className="mb-3"
              // onClick={() => toggleReviewState()}
              variant="secondary"
            >
              Add all files to request
            </Button>
          ) : null}
          <FileList
            authToken={authToken}
            checkedIds={checkedIds}
            filesUrl={filesUrl}
            isReviewEdit={isReviewEdit}
            listVisible={listVisible}
            selectedFile={selectedFile}
            setListVisible={setListVisible}
            setSelectedFile={setSelectedFile}
          />
        </Col>
        <Col lg={9}>
          {selectedFile && (
            <>
              {isReviewEdit ? (
                <Button
                  className="mb-3"
                  onClick={() => {
                    if (checkedIds.includes(selectedFile.id)) {
                      return setCheckedIds(
                        checkedIds.filter((f) => f !== selectedFile.id)
                      );
                    }
                    return setCheckedIds([...checkedIds, selectedFile.id]);
                  }}
                  variant={
                    checkedIds.includes(selectedFile.id) ? "danger" : "success"
                  }
                >
                  {checkedIds.includes(selectedFile.id)
                    ? "Remove file from review request"
                    : "Add file to review request"}
                </Button>
              ) : null}

              <Card>
                <Metadata
                  fileDate={selectedFile.date}
                  fileName={selectedFile.name}
                  fileSize={selectedFile.size}
                  fileUrl={selectedFile.url}
                />
                <Card.Body>
                  <Viewer
                    authToken={authToken}
                    fileName={selectedFile.name}
                    fileShortName={selectedFile.shortName}
                    fileSize={selectedFile.size}
                    fileUrl={selectedFile.url}
                    uuid={uuid}
                  />
                </Card.Body>
              </Card>
            </>
          )}
        </Col>
      </Row>
      <Toast />
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  );
}

export default App;

App.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  csrfToken: datasetProps.csrfToken.isRequired,
  filesUrl: datasetProps.filesUrl.isRequired,
  prepareUrl: datasetProps.prepareUrl,
  publishUrl: datasetProps.publishUrl,
  reviewUrl: datasetProps.reviewUrl.isRequired,
};

App.defaultProps = {
  prepareUrl: null,
  publishUrl: null,
};
