import PropTypes from "prop-types";
import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import FileList from "./components/FileList/FileList";
import PrepareButton from "./components/PrepareButton/PrepareButton";
import PublishButton from "./components/PublishButton/PublishButton";
import Viewer from "./components/Viewer/Viewer";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: Infinity,
    },
  },
});

function App({ csrfToken, filesUrl, prepareUrl, publishUrl }) {
  const [listVisible, setListVisible] = useState(false);
  const [file, setFile] = useState({ name: "", url: "" });

  return (
    <QueryClientProvider client={queryClient}>
      {prepareUrl && (
        <div className="row">
          <div className="col">
            <PrepareButton
              csrfToken={csrfToken}
              filesUrl={filesUrl}
              prepareUrl={prepareUrl}
            />
          </div>
        </div>
      )}
      {publishUrl && (
        <div className="row">
          <div className="col">
            <PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />
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
            apiUrl={filesUrl}
            listVisible={listVisible}
            setFile={setFile}
            setListVisible={setListVisible}
          />
        </div>
        <div className="col-lg-9">
          <Viewer file={file} />
        </div>
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;

App.propTypes = {
  csrfToken: PropTypes.string,
  filesUrl: PropTypes.string.isRequired,
  prepareUrl: PropTypes.string,
  publishUrl: PropTypes.string,
};

App.defaultProps = {
  csrfToken: null,
  prepareUrl: null,
  publishUrl: null,
};
