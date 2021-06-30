import React from "react";
import { QueryClient, QueryClientProvider, useQuery } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

function FileList() {
  const { isLoading, isError, data, error } = useQuery(
    "FILE_LIST",
    () => fetch("/"),
    {
      initialData: window.props,
      staleTime: Infinity,
    }
  );

  if (isLoading) {
    return <span>Loading...</span>;
  }

  if (isError) {
    return <span>Error: {error.message}</span>;
  }

  return <h1>{data.name}</h1>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <FileList />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
