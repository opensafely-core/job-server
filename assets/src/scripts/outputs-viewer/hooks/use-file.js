import { useQuery } from "react-query";
import handleErrors from "../utils/fetch-handle-errors";
import { canDisplay } from "../utils/file-type-match";

function useFile(file) {
  return useQuery(["FILE", file.url], async () => {
    // If we can't display the file type
    // or the file size is too large
    // don't try to return the data
    if (!canDisplay(file) || file.size > 20000000) return {};

    return fetch(file.url)
      .then(handleErrors)
      .then(async (response) => response.text());
  });
}

export default useFile;
