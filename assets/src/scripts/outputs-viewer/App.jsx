import {
  QueryClient,
  QueryClientProvider,
  QueryCache,
} from "@tanstack/react-query";
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
import { toastError } from "./utils/toast";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (query.meta.errorMessage) {
        toastError({
          message: query.meta.errorMessage,
          toastId: query.meta.id,
          filesUrl: query.meta.id,
          url: document.location.href,
        });
      }
    },
  }),
});

function App({
  authToken,
  csrfToken,
  filesUrl,
  prepareUrl = null,
  publishUrl = null,
}) {
  const uuid = Date.now();
  const [listVisible, setListVisible] = useState(true);
  const [selectedFile, setSelectedFile] = useState();

  return (
    <QueryClientProvider client={queryClient}>
      <div className="py-6">
        {(prepareUrl || publishUrl) && (
          <div className="mb-3 -mt-3 px-1 md:px-6">
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
        )}
        <div className="grid gap-6 grid-cols-1 px-1 md:grid-cols-3 md:px-6 lg:grid-cols-4">
          <div className="flex flex-col gap-y-1 md:col-span-1">
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
          <div className="md:col-span-2 lg:col-span-3">
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
