import { useQuery } from "react-query";
import handleErrors from "./fetch-handle-errors";
import { canDisplay } from "./file-type-match";

function useFile(file) {
  return useQuery(["FILE", file.url], async () => {
    if (!canDisplay(file)) return {};

    return fetch(file.url)
      .then(handleErrors)
      .then(async (response) => response.text());
  });
}

export default useFile;
