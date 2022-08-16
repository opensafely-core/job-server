import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React, { useState } from "react";
import { BrowserRouter } from "react-router-dom";
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

function App({
  authToken = "",
  basePath,
  csrfToken,
  filesUrl,
  prepareUrl,
  publishUrl,
}) {
  const uuid = Date.now();
  const [listVisible, setListVisible] = useState(true);
  const [selectedFile, setSelectedFile] = useState();

  return (
    <BrowserRouter basename={basePath}>
      <QueryClientProvider client={queryClient}>
        {(prepareUrl || publishUrl) && (
          <div className="row mb-2">
            <div className="col">
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
            </div>
          </div>
        )}
        <div className="row mb-3">
          <div className="col-lg-3">
            <button
              className="d-block d-lg-none btn btn-secondary mb-3"
              onClick={() => setListVisible(!listVisible)}
              type="button"
            >
              {listVisible ? "Hide" : "Show"} file list
            </button>
            <FileList
              authToken={authToken}
              filesUrl={filesUrl}
              listVisible={listVisible}
              setListVisible={setListVisible}
              setSelectedFile={setSelectedFile}
            />
          </div>
          <div className="col-lg-9">
            {selectedFile && (
              <div className="card">
                <Metadata
                  fileDate={selectedFile.date}
                  fileName={selectedFile.name}
                  fileSize={selectedFile.size}
                  fileUrl={selectedFile.url}
                />
                <div className="card-body">
                  <Viewer
                    authToken={authToken}
                    fileName={selectedFile.name}
                    fileShortName={selectedFile.shortName}
                    fileSize={selectedFile.size}
                    fileUrl={selectedFile.url}
                    uuid={uuid}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
        <Toast />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </BrowserRouter>
  );
}

export default App;

App.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  basePath: datasetProps.basePath.isRequired,
  csrfToken: datasetProps.csrfToken.isRequired,
  filesUrl: datasetProps.filesUrl.isRequired,
  prepareUrl: datasetProps.prepareUrl.isRequired,
  publishUrl: datasetProps.publishUrl.isRequired,
};
