import { useQuery } from "@tanstack/react-query";
import { toastError } from "../utils/toast";

export function sortedFiles(files) {
  return [
    ...files
      .sort((a, b) => {
        const nameA = a.name.toUpperCase();
        const nameB = b.name.toUpperCase();

        if (nameA < nameB) return -1;
        if (nameA > nameB) return 1;
        return 0;
      })
      .map((file) => ({ ...file })),
  ];
}

function useFileList({ authToken, filesUrl }) {
  return useQuery(
    ["FILE_LIST"],
    async () => {
      const response = await fetch(filesUrl, {
        headers: {
          Authorization: authToken,
        },
      });

      if (!response.ok) throw new Error();

      return response.json();
    },
    {
      select: (data) => sortedFiles(data.files),
      onError: () => {
        toastError({
          message: "Unable to load files",
          toastId: filesUrl,
          filesUrl,
          url: document.location.href,
        });
      },
    }
  );
}

export default useFileList;
