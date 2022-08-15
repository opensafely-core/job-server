import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React, { useState } from "react";
import { BrowserRouter } from "react-router-dom";
import PrepareButton from "./components/Button/PrepareButton";
import PublishButton from "./components/Button/PublishButton";
import FileList from "./components/FileList/FileList";
import Toast from "./components/Toast/Toast";
import Viewer from "./components/Viewer/Viewer";
import { useFiles } from "./context/FilesProvider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const {
    state: { basePath, prepareUrl, publishUrl },
  } = useFiles();
  const [listVisible, setListVisible] = useState(true);
  const hasButtons = prepareUrl || publishUrl;

  return (
    <BrowserRouter basename={basePath}>
      <QueryClientProvider client={queryClient}>
        {hasButtons && (
          <div className="row mb-2">
            <div className="col">
              {prepareUrl && <PrepareButton />}
              {publishUrl && <PublishButton />}
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
              listVisible={listVisible}
              setListVisible={setListVisible}
            />
          </div>
          <div className="col-lg-9">
            <Viewer />
          </div>
        </div>
        <Toast />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </BrowserRouter>
  );
}

export default App;
