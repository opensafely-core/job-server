import { useQuery } from "react-query";
import useStore from "../stores/use-store";
import handleErrors from "../utils/fetch-handle-errors";
import { canDisplay } from "../utils/file-type-match";

function useFile(file) {
  const { authToken } = useStore();

  return useQuery(["FILE", file.url], async () => {
    // If we can't display the file type
    // or the file size is too large
    // don't try to return the data
    if (!canDisplay(file) || file.size > 20000000) return {};

    return fetch(file.url, {
      headers: new Headers({
        Authorization: authToken,
      }),
    })
      .then(handleErrors)
      .then(async (response) => response.text());
  });
}

export default useFile;
