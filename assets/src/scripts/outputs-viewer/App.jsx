import PropTypes from "prop-types";
import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
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

function App({ dataset }) {
  const [file, setFile] = useState({ name: "", url: "" });

  return (
    <QueryClientProvider client={queryClient}>
      <div className="row">
        <div className="col-md-3">
          <FileList apiUrl={dataset.apiUrl} setFile={setFile} />
        </div>
        <div className="col-md-9">
          <h1 className="h2">
            {dataset.workspaceName}:{" "}
            <pre className="d-inline">{dataset.releaseName}</pre>
          </h1>
          <ul className="list-unstyled">
            <li>
              <strong>Author:</strong> {dataset.releaseAuthor}
            </li>
            <li>
              <strong>Created:</strong> {dataset.releaseDate}
            </li>
          </ul>
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
  dataset: PropTypes.objectOf({
    apiUrl: PropTypes.string.isRequired,
    releaseName: PropTypes.string.isRequired,
    releaseAuthor: PropTypes.string.isRequired,
    releaseDate: PropTypes.string.isRequired,
  }).isRequired,
};
