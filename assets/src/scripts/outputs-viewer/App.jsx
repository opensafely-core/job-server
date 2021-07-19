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
    input: "MMMM d, yyyy, h:m bbbb xxxx",
  });

  return (
    <QueryClientProvider client={queryClient}>
      <div className="row">
        <div className="col-md-3">
          <FileList apiUrl={dataset.apiUrl} setFile={setFile} />
        </div>
        <div className="col-md-9">
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
