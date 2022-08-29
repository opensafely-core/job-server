import React, { useEffect, useState } from "react";
import { Button, Card, Col, Row } from "react-bootstrap";
import PrepareButton from "./components/Button/PrepareButton";
import PublishButton from "./components/Button/PublishButton";
import FileList from "./components/FileList/FileList";
import FileReview from "./components/FileReview/FileReview";
import Metadata from "./components/Metadata/Metadata";
import ReviewModal from "./components/Review/Modal";
import Toast from "./components/Toast/Toast";
import Viewer from "./components/Viewer/Viewer";
import useReviewState from "./hooks/use-review-state";
import useAppStore from "./stores/use-app-store";
import useFileStore from "./stores/use-file-store";
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
  const { showModal, isModalOpen } = useAppStore((state) => ({
    showModal: state.showModal,
    isModalOpen: state.isModalOpen,
  }));
  const checkedFiles = useFileStore((state) => state.checkedFiles);
  const removeAllCheckedFiles = useFileStore(
    (state) => state.removeAllCheckedFiles
  );
  const { isReviewEdit, isReviewView, setReviewEdit, setReviewView } =
    useReviewState();

  const isReview = !!reviewUrl;

  useEffect(
    () =>
      useAppStore.setState({
        authToken,
        csrfToken,
        filesUrl,
        prepareUrl,
        publishUrl,
        reviewUrl,
      }),
    [] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <>
      {isReview && (
        <>
          {isModalOpen && <ReviewModal />}
          <Row>
            <Col className="d-flex mb-3">
              {isReviewView ? (
                <Button
                  className="ml-auto"
                  onClick={() => setReviewEdit()}
                  variant="success"
                >
                  Prepare a review request
                </Button>
              ) : null}

              {isReviewEdit ? (
                <>
                  <Button
                    className="ml-auto"
                    disabled={!checkedFiles.length}
                    onClick={() => showModal()}
                    variant="success"
                  >
                    Submit review request
                  </Button>
                  <Button
                    className="ml-2"
                    onClick={() => {
                      setReviewView();
                      removeAllCheckedFiles();
                    }}
                    variant="danger"
                  >
                    Cancel review request
                  </Button>
                </>
              ) : null}
            </Col>
          </Row>
        </>
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
          {/* {isReview && isReviewEdit ? <ToggleFileReview /> : null} */}
          <FileList
            authToken={authToken}
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
              {isReviewEdit ? <FileReview selectedFile={selectedFile} /> : null}
              <Card>
                <Metadata
                  fileDate={selectedFile.date}
                  fileName={selectedFile.name}
                  fileSize={selectedFile.size}
                  fileUrl={selectedFile.url}
                  metadata={selectedFile.metadata}
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
  reviewUrl: datasetProps.reviewUrl,
};

App.defaultProps = {
  prepareUrl: null,
  publishUrl: null,
  reviewUrl: null,
};
