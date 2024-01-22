import { useQuery } from "@tanstack/react-query";

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
  const filesSorted = [...files]
    .sort((a, b) => b.date.localeCompare(a.date))
    .map((item, i) => ({
      dateOrder: i,
      ...item,
    }))
    .sort((a, b) =>
      enCollator.compare(a.name.toUpperCase(), b.name.toUpperCase()),
    )
    .map((item, i) => ({ nameOrder: i, ...item }));

  if (filesSorted.length < 2) {
    return filesSorted.map((file) => ({
      ...file,
      shortName: file.name,
    }));
  }

  const prefix = longestSubStr(filesSorted);

  return filesSorted.map((file) => ({
    ...file,
    shortName: file.name.replace(`${prefix}/`, ""),
    visible: true,
  }));
}

function useFileList({ authToken, filesUrl }) {
  return useQuery({
    queryKey: ["FILE_LIST"],
    queryFn: async () => {
      const response = await fetch(filesUrl, {
        headers: {
          Authorization: authToken,
        },
      });

      if (!response.ok) throw new Error("File list not found");

      return response.json();
    },
    select: (data) => sortedFiles(data.files),
    meta: {
      errorMessage: "Unable to load files",
      id: filesUrl,
    },
  });
}

export default useFileList;
