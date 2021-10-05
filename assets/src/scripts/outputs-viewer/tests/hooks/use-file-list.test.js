import { longestStartingSubstr, sortedFiles } from "../../hooks/use-file-list";

describe("useFileList hook", () => {
  const unordered = [
    { name: "B" },
    { name: "A" },
    { name: "C" },
    { name: "C" },
  ];
  const ordered = [
    { name: "A", shortName: "A" },
    { name: "B", shortName: "B" },
    { name: "C", shortName: "C" },
    { name: "C", shortName: "C" },
  ];

  it("sorts files by name", () => {
    expect(sortedFiles(unordered)).toEqual(ordered);
  });

  it("finds the longest prefix string", () => {
    expect(longestStartingSubstr(["data-001.csv", "data-002.csv"])).toEqual(
      "data-00"
    );

    expect(longestStartingSubstr(["nodata-001.csv", "data-002.csv"])).toEqual(
      ""
    );

    expect(longestStartingSubstr(["data-001.csv"])).toEqual("");
  });
});
