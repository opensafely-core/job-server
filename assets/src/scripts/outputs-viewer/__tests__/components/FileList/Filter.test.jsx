import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import Filter from "../../../components/FileList/Filter";
import {
  csvFile,
  fileList,
  htmlFile,
  pngFile,
  txtFile,
} from "../../helpers/files";
import { render, screen, waitFor } from "../../test-utils";

describe("<Filter />", () => {
  const setFiles = vi.fn();
  const listRef = vi.fn();

  it("shows the filter", async () => {
    render(<Filter files={fileList} listRef={listRef} setFiles={setFiles} />);

    expect(
      screen.getByRole("searchbox", { name: "Find a file…" }),
    ).toBeVisible();
  });

  it("filters on text input", async () => {
    const user = userEvent.setup();
    render(<Filter files={fileList} listRef={listRef} setFiles={setFiles} />);

    const searchbox = screen.getByRole("searchbox", { name: "Find a file…" });
    expect(searchbox).toBeVisible();
    await user.type(searchbox, "html");

    await waitFor(() =>
      expect(setFiles).toHaveBeenLastCalledWith([
        { ...csvFile, visible: false },
        { ...pngFile, visible: false },
        { ...txtFile, visible: false },
        { ...htmlFile, visible: true },
      ]),
    );
  });

  it("clears filter on clearing of input", async () => {
    const user = userEvent.setup();
    render(<Filter files={fileList} listRef={listRef} setFiles={setFiles} />);

    const searchbox = screen.getByRole("searchbox", { name: "Find a file…" });
    expect(searchbox).toBeVisible();
    await user.type(searchbox, "html");

    await waitFor(() =>
      expect(setFiles).toHaveBeenLastCalledWith([
        { ...csvFile, visible: false },
        { ...pngFile, visible: false },
        { ...txtFile, visible: false },
        { ...htmlFile, visible: true },
      ]),
    );

    await user.clear(searchbox);

    await waitFor(() => expect(setFiles).toHaveBeenLastCalledWith(fileList));
  });
});
