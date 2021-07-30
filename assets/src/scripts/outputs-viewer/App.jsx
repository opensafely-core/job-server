import PropTypes from "prop-types";
import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import PrepareButton from "./components/Button/PrepareButton";
import PublishButton from "./components/Button/PublishButton";
import FileList from "./components/FileList/FileList";
import Viewer from "./components/Viewer/Viewer";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: Infinity,
    },
  },
});

function App({ authToken, csrfToken, filesUrl, prepareUrl, publishUrl }) {
  const [listVisible, setListVisible] = useState(false);
  const [file, setFile] = useState({ name: "", url: "" });
  const hasButtons = prepareUrl || publishUrl;

  return (
    <QueryClientProvider client={queryClient}>
      {hasButtons && (
        <div className="row">
          <div className="col">
            {prepareUrl && (
              <PrepareButton
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
            apiUrl={filesUrl}
            authToken={authToken}
            listVisible={listVisible}
            setFile={setFile}
            setListVisible={setListVisible}
          />
        </div>
        <div className="col-lg-9">
          <Viewer authToken={authToken} file={file} />
        </div>
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;

App.propTypes = {
  authToken: PropTypes.string,
  csrfToken: PropTypes.string,
  filesUrl: PropTypes.string.isRequired,
  prepareUrl: PropTypes.string,
  publishUrl: PropTypes.string,
};

App.defaultProps = {
  authToken: null,
  csrfToken: null,
  prepareUrl: null,
  publishUrl: null,
};
