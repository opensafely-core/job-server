import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import useFileList, { sortedFiles } from "../../hooks/use-file-list";
import { pngFile } from "../helpers/files";

describe("useFileList hook", () => {
  const unordered = [
    { name: "a/b", date: "2024-01-12T12:00:00.000000+00:00" },
    { name: "a/A", date: "2024-01-13T12:00:00.000000+00:00" },
    { name: "a/C", date: "2024-01-14T12:00:00.000000+00:00" },
    { name: "a/C", date: "2024-01-15T12:00:00.000000+00:00" },
  ];
  const ordered = [
    {
      date: "2024-01-13T12:00:00.000000+00:00",
      dateOrder: 2,
      name: "a/A",
      nameOrder: 0,
      shortName: "A",
      visible: true,
    },
    {
      date: "2024-01-12T12:00:00.000000+00:00",
      dateOrder: 3,
      name: "a/b",
      nameOrder: 1,
      shortName: "b",
      visible: true,
    },
    {
      date: "2024-01-15T12:00:00.000000+00:00",
      dateOrder: 0,
      name: "a/C",
      nameOrder: 2,
      shortName: "C",
      visible: true,
    },
    {
      date: "2024-01-14T12:00:00.000000+00:00",
      dateOrder: 1,
      name: "a/C",
      nameOrder: 3,
      shortName: "C",
      visible: true,
    },
  ];

  it("sorts files by name", () => {
    expect(sortedFiles(unordered)).toEqual(ordered);
  });

  it("returns full name for a list of only one file", () => {
    expect(sortedFiles([pngFile])).toEqual([
      {
        ...pngFile,
        dateOrder: 0,
        nameOrder: 0,
        shortName: pngFile.name,
      },
    ]);
  });

  it("throws an error if the files URL does not work", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    const wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    fetch.mockResponseOnce("{}", {
      status: 500,
      headers: { "content-type": "application/json" },
    });
    const { result } = renderHook(
      () =>
        useFileList({
          authToken: "use-file-list.test",
          filesUrl: "use-file-list.test.js",
        }),
      { wrapper },
    );

    waitFor(() =>
      expect(result.current.error).toEqual(new Error("File list not found")),
    );
  });
});
