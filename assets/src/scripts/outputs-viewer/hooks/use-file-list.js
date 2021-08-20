import axios from "axios";
import { useQuery } from "react-query";
import useStore from "../stores/use-store";
import { toastError } from "../utils/toast";

export function longestStartingSubstr(array) {
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
  const { filesUrl, authToken } = useStore();

  return useQuery(
    "FILE_LIST",
    async () =>
      axios
        .get(filesUrl, {
          headers: {
            Authorization: authToken,
          },
        })
        .then((response) => response.data)
        .catch((error) => {
          throw error?.response?.data?.detail || error.toJSON().message;
        }),
    {
      select: (data) => sortedFiles(data.files),
      onError: (error) => {
        toastError({
          message: `${error}`,
          toastId: filesUrl,
          filesUrl,
          url: document.location.href,
        });
      },
    }
  );
}

export default useFileList;
