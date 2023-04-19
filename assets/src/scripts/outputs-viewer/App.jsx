import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React, { useState } from "react";
import { Button, Card, Col, Row } from "react-bootstrap";
import PrepareButton from "./components/Button/PrepareButton";
import PublishButton from "./components/Button/PublishButton";
import FileList from "./components/FileList/FileList";
import Metadata from "./components/Metadata/Metadata";
import Toast from "./components/Toast/Toast";
import Viewer from "./components/Viewer/Viewer";
import { datasetProps } from "./utils/props";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

function App({ authToken, csrfToken, filesUrl, prepareUrl, publishUrl }) {
  const uuid = Date.now();
  const [listVisible, setListVisible] = useState(true);
  const [selectedFile, setSelectedFile] = useState();

  return (
    <QueryClientProvider client={queryClient}>
      {(prepareUrl || publishUrl) && (
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
      )}
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
          <FileList
            authToken={authToken}
            filesUrl={filesUrl}
            listVisible={listVisible}
            setListVisible={setListVisible}
            setSelectedFile={setSelectedFile}
          />
        </Col>
        <Col lg={9}>
          {selectedFile && (
            <Card>
              <Card.Header>
                <Metadata
                  fileDate={selectedFile.date}
                  fileName={selectedFile.name}
                  fileSize={selectedFile.size}
                  fileUrl={selectedFile.url}
                />
              </Card.Header>
              <Card.Body>
                <Viewer
                  authToken={authToken}
                  fileName={selectedFile.name}
                  fileSize={selectedFile.size}
                  fileUrl={selectedFile.url}
                  uuid={uuid}
                />
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>
      <Toast />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;

App.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  csrfToken: datasetProps.csrfToken.isRequired,
  filesUrl: datasetProps.filesUrl.isRequired,
  prepareUrl: datasetProps.prepareUrl,
  publishUrl: datasetProps.publishUrl,
};

App.defaultProps = {
  prepareUrl: null,
  publishUrl: null,
};
