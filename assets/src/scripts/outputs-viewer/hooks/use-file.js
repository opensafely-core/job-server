import { useQuery } from "react-query";
import useStore from "../stores/use-store";
import handleErrors from "../utils/fetch-handle-errors";
import { canDisplay, isCsv, isImg } from "../utils/file-type-match";

function convertBlobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      resolve(reader.result);
    };
    reader.readAsDataURL(blob);
  });
}

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
    // grab the blob and encode it as Base64
    if (isImg(file))
      return fetch(file.url, {
        headers: new Headers({
          Authorization: authToken,
        }),
      })
        .then(handleErrors)
        .then(async (response) => response.blob())
        .then((blob) => convertBlobToBase64(blob));

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
