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

function App({ apiUrl }) {
  const [listVisible, setListVisible] = useState(false);
  const [file, setFile] = useState({ name: "", url: "" });

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
            apiUrl={apiUrl}
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
  apiUrl: PropTypes.string.isRequired,
};
