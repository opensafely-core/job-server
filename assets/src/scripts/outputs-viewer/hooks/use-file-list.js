import { useQuery } from "@tanstack/react-query";
import { useFiles } from "../context/FilesProvider";
import { toastError } from "../utils/toast";

export function longestStartingSubstr(array) {
  if (array.length < 2) {
    // don't match the entire string for single item arrays
    return "";
  }

  const A = array.concat().sort();
  const a1 = A[0];
  const a2 = A[A.length - 1];
  const L = a1.length;
  let i = 0;
  while (i < L && a1.charAt(i) === a2.charAt(i)) i += 1;
  return a1.substring(0, i);
}

export function sortedFiles(files) {
  const fileNameArr = [...files].map((file) => file.name);
  const prefix = longestStartingSubstr(fileNameArr);

  return [
    ...files
      .sort((a, b) => {
        const nameA = a.name.toUpperCase();
        const nameB = b.name.toUpperCase();

        if (nameA < nameB) return -1;
        if (nameA > nameB) return 1;
        return 0;
      })
      .map((file) => ({ ...file, shortName: file.name.replace(prefix, "") })),
  ];
}

function useFileList() {
  const {
    state: { filesUrl, authToken },
  } = useFiles();

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
