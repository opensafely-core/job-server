import PropTypes from "prop-types";
import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import FileList from "./components/FileList/FileList";
import Viewer from "./components/Viewer/Viewer";
import dateFmt from "./utils/date-format";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: Infinity,
    },
  },
});

function App({ dataset }) {
  const [listVisible, setListVisible] = useState(false);
  const [file, setFile] = useState({ name: "", url: "" });
  const releaseDate = dateFmt({
    date: `${dataset.releaseDate} +0000`,
    input: "MMMM d, yyyy, h:m bbbb xxxx",
  });

  return (
    <QueryClientProvider client={queryClient}>
      <div className="row">
        <div className="col-lg-3">
          <button
            className="d-block d-lg-none btn btn-secondary mb-3"
            onClick={() => setListVisible(!listVisible)}
            type="button"
          >
            {listVisible ? "Hide" : "Show"} file list
          </button>
          <FileList
            apiUrl={dataset.apiUrl}
            listVisible={listVisible}
            setFile={setFile}
            setListVisible={setListVisible}
          />
        </div>
        <div className="col-lg-9">
          <h1 className="card-title h3">
            {dataset.workspaceName}:{" "}
            <pre className="d-inline">{dataset.releaseName}</pre>
          </h1>
          <p className="card-subtitle mb-2 text-muted">
            Released by {dataset.releaseAuthor} on {releaseDate}
          </p>
          <hr />
          <Viewer file={file} />
        </div>
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;

App.propTypes = {
  dataset: PropTypes.shape({
    apiUrl: PropTypes.string.isRequired,
    releaseName: PropTypes.string.isRequired,
    releaseAuthor: PropTypes.string.isRequired,
    releaseDate: PropTypes.string.isRequired,
    workspaceName: PropTypes.string.isRequired,
  }).isRequired,
};
