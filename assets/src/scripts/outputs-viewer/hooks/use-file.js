import { useQuery } from "react-query";
import useStore from "../stores/use-store";
import handleErrors from "../utils/fetch-handle-errors";
import { canDisplay, isCsv, isImg } from "../utils/file-type-match";

function useFile(file) {
  const { authToken } = useStore();

  return useQuery(["FILE", file.url], async () => {
    // If we can't display the file type
    // or the file size is too large (>20mb)
    // don't try to return the data
    if (!canDisplay(file) || file.size > 20000000) return {};

    // If the file is a CSV
    // and the file size is too large (>5mb)
    // don't try to return the data
    if (isCsv(file) && file.size > 5000000) return {};

    // If the file is an image
    // we don't need the data, only the URL
    if (isImg(file)) return { data: file.url };

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
