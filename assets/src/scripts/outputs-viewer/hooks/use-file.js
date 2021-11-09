import axios from "axios";
import { useQuery } from "react-query";
import { useFiles } from "../context/FilesProvider";
import { canDisplay, isCsv, isImg } from "../utils/file-type-match";
import { toastError } from "../utils/toast";

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
  const {
    state: { authToken },
  } = useFiles();

  return useQuery(
    ["FILE", file.url],
    async () => {
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
        return axios
          .get(file.url, {
            headers: {
              Authorization: authToken,
            },
            responseType: "blob",
          })
          .then((response) => response.data)
          .then((blob) => convertBlobToBase64(blob))
          .catch((error) => {
            throw error?.response?.data?.detail || error?.message;
          });

      return axios
        .get(file.url, {
          headers: {
            Authorization: authToken,
          },
        })
        .then((response) => response.data)
        .catch((error) => {
          throw error?.response?.data?.detail || error?.message;
        });
    },
    {
      onError: (error) => {
        toastError({
          message: `${file.shortName} - ${error}`,
          toastId: file.url,
          fileUrl: file.url,
          url: document.location.href,
        });
      },
    }
  );
}

export default useFile;
