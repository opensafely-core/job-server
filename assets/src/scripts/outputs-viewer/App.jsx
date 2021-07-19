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
  const [file, setFile] = useState({ name: "", url: "" });
  const releaseDate = dateFmt({
    date: `${dataset.releaseDate} +0000`,
    format: "MMMM d, yyyy, h:m bbbb xxxx",
  });

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
              <strong>Created:</strong> {releaseDate}
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
  dataset: PropTypes.shape({
    apiUrl: PropTypes.string.isRequired,
    releaseName: PropTypes.string.isRequired,
    releaseAuthor: PropTypes.string.isRequired,
    releaseDate: PropTypes.string.isRequired,
    workspaceName: PropTypes.string.isRequired,
  }).isRequired,
};
