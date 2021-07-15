import { useQuery } from "react-query";
import handleErrors from "./fetch-handle-errors";

function useFile(fileUrl) {
  return useQuery(["FILE", fileUrl], async () =>
    fetch(fileUrl)
      .then(handleErrors)
      .then(async (response) => response.text())
  );
}

export default useFile;
