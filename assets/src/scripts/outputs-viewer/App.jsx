import React from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import PrepareButton from "./components/Button/PrepareButton";
import PublishButton from "./components/Button/PublishButton";
import FileList from "./components/FileList/FileList";
import Viewer from "./components/Viewer/Viewer";
import useStore from "./stores/use-store";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: Infinity,
    },
  },
});

function App() {
  const { listVisible, prepareUrl, publishUrl } = useStore();
  const hasButtons = prepareUrl || publishUrl;

  return (
    <QueryClientProvider client={queryClient}>
      {hasButtons && (
        <div className="row">
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
            onClick={() => useStore.setState({ listVisible: !listVisible })}
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
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
