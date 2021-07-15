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
  const [fileUrl, setFileUrl] = useState("");

  return (
    <QueryClientProvider client={queryClient}>
      <div className="row">
        <div className="col-md-3">
          <FileList apiUrl={apiUrl} setFileUrl={setFileUrl} />
        </div>
        <div className="col-md-9">
          <Viewer fileUrl={fileUrl} />
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
