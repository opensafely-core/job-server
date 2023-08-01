import { useQuery } from "@tanstack/react-query";
import { toastError } from "../utils/toast";

function longestSubStr(files) {
  let initialStr = [];
  let newStr = [];

  files.map((file, i) => {
    const splitFileName = file.name.split("/");
    if (i === 0) {
      initialStr = [];
      // eslint-disable-next-line no-return-assign
      return (initialStr = splitFileName);
    }

    newStr = [];
    return splitFileName.map((value, index) => {
      if (value === initialStr[index]) {
        return newStr.push(value);
      }
      return null;
    });
  });

  return newStr.join("/");
}

export function sortedFiles(files) {
  const enCollator = new Intl.Collator("en");
  const filesSorted = [...files].sort((a, b) =>
    enCollator.compare(a.name.toUpperCase(), b.name.toUpperCase()),
  );

  if (filesSorted.length < 2) return filesSorted;

  const prefix = longestSubStr(filesSorted);

  return filesSorted.map((file) => ({
    ...file,
    shortName: file.name.replace(`${prefix}/`, ""),
  }));
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
    },
  );
}

export default useFileList;
