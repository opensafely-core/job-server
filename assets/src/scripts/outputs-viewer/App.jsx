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
  const [file, setFile] = useState({ name: "", url: "" });

  return (
    <QueryClientProvider client={queryClient}>
      <div className="row">
        <div className="col-md-3">
          <FileList apiUrl={apiUrl} setFile={setFile} />
        </div>
        <div className="col-md-9">
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
