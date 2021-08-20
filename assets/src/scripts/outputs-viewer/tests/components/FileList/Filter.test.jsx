import userEvent from "@testing-library/user-event";
import React from "react";
import Filter from "../../../components/FileList/Filter";
import { fileList, htmlFile } from "../../helpers/files";
import { render, screen, waitFor } from "../../test-utils";

describe("<Filter />", () => {
  const setFiles = jest.fn();
  const listRef = jest.fn();

  it("shows the filter", async () => {
    render(<Filter files={fileList} listRef={listRef} setFiles={setFiles} />);

    expect(
      screen.getByRole("searchbox", { name: "Find a file…" })
    ).toBeVisible();
  });

  it("filters on text input", async () => {
    render(<Filter files={fileList} listRef={listRef} setFiles={setFiles} />);

    const searchbox = screen.getByRole("searchbox", { name: "Find a file…" });
    expect(searchbox).toBeVisible();
    userEvent.type(searchbox, "html");

    await waitFor(() => expect(setFiles).toHaveBeenLastCalledWith([htmlFile]));
  });

  it("clears filter on clearing of input", async () => {
    render(<Filter files={fileList} listRef={listRef} setFiles={setFiles} />);

    const searchbox = screen.getByRole("searchbox", { name: "Find a file…" });
    expect(searchbox).toBeVisible();
    userEvent.type(searchbox, "html");

    await waitFor(() => expect(setFiles).toHaveBeenLastCalledWith([htmlFile]));

    userEvent.clear(searchbox);

    await waitFor(() => expect(setFiles).toHaveBeenLastCalledWith(fileList));
  });
});
