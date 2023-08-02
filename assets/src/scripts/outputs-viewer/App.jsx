import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React, { useState } from "react";
import Button from "./components/Button/Button";
import PrepareButton from "./components/Button/PrepareButton";
import PublishButton from "./components/Button/PublishButton";
import Card from "./components/Card";
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
      <div className="container py-6">
        <div className="grid gap-6 grid-cols-1 md:grid-cols-3 lg:grid-cols-4">
          <div className="flex flex-col gap-y-1 col-span-1">
            {(prepareUrl || publishUrl) && (
              <>
                {prepareUrl && (
                  <PrepareButton
                    authToken={authToken}
                    csrfToken={csrfToken}
                    filesUrl={filesUrl}
                    prepareUrl={prepareUrl}
                  />
                )}
                {publishUrl && (
                  <PublishButton
                    csrfToken={csrfToken}
                    publishUrl={publishUrl}
                  />
                )}
              </>
            )}
            <Button
              className="block md:hidden mb-3"
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
          </div>
          <div className="col-span-2 lg:col-span-3">
            {selectedFile && (
              <Card
                container
                header={
                  <Metadata
                    fileDate={selectedFile.date}
                    fileName={selectedFile.shortName}
                    fileSize={selectedFile.size}
                    fileUrl={selectedFile.url}
                  />
                }
              >
                <Viewer
                  authToken={authToken}
                  fileName={selectedFile.shortName}
                  fileSize={selectedFile.size}
                  fileUrl={selectedFile.url}
                  uuid={uuid}
                />
              </Card>
            )}
          </div>
        </div>
      </div>
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
