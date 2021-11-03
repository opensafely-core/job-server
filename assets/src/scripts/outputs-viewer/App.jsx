import React from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
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
      staleTime: Infinity,
    },
  },
});

function App() {
  const {
    dispatch,
    state: { basePath, listVisible, prepareUrl, publishUrl },
  } = useFiles();
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
              onClick={() =>
                dispatch({
                  type: "update",
                  state: { listVisible: !listVisible },
                })
              }
              type="button"
            >
              {listVisible ? "Hide" : "Show"} file list
            </button>
            <FileList />
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
