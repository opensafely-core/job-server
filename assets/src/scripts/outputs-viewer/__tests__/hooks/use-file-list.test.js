import { describe, expect, it } from "vitest";
import { sortedFiles } from "../../hooks/use-file-list";

describe("useFileList hook", () => {
  const unordered = [
    { name: "b" },
    { name: "A" },
    { name: "C" },
    { name: "C" },
  ];
  const ordered = [{ name: "A" }, { name: "b" }, { name: "C" }, { name: "C" }];

  it("sorts files by name", () => {
    expect(sortedFiles(unordered)).toEqual(ordered);
  });
});
