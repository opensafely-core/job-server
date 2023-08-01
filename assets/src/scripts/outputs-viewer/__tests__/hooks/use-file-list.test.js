import { describe, expect, it } from "vitest";
import { sortedFiles } from "../../hooks/use-file-list";

describe("useFileList hook", () => {
  const unordered = [
    { name: "a/b" },
    { name: "a/A" },
    { name: "a/C" },
    { name: "a/C" },
  ];
  const ordered = [
    { name: "a/A", shortName: "A" },
    { name: "a/b", shortName: "b" },
    { name: "a/C", shortName: "C" },
    { name: "a/C", shortName: "C" },
  ];

  it("sorts files by name", () => {
    expect(sortedFiles(unordered)).toEqual(ordered);
  });
});
