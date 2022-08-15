import { useQuery } from "@tanstack/react-query";
import { useFiles } from "../context/FilesProvider";
import { canDisplay, isCsv, isImg } from "../utils/file-type-match";
import { toastError } from "../utils/toast";

function useFile(file) {
  const {
    state: { authToken, uuid },
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

      // Combine file URL with UUID
      const fileURL = `${file.url}?${uuid}`;

      const response = await fetch(fileURL, {
        headers: {
          Authorization: authToken,
        },
      });

      if (!response.ok) throw new Error();

      // If the file is an image
      // grab the blob and create a URL for the blob
      if (isImg(file)) {
        const blob = await response.blob();
        return URL.createObjectURL(blob);
      }

      // Otherwise return the text of the data
      return response.text();
    },
    {
      onError: () => {
        toastError({
          message: `${file.shortName} - Unable to load file`,
          toastId: file.url,
          fileUrl: file.url,
          url: document.location.href,
        });
      },
    }
  );
}

export default useFile;
