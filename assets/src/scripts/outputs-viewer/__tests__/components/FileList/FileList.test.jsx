import userEvent from "@testing-library/user-event";
import React, { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import FileList from "../../../components/FileList/FileList";
import {
  csvFile,
  fileList,
  htmlFile,
  pngFile,
  txtFile,
} from "../../helpers/files";
import props from "../../helpers/props";
import { history, render, screen, waitFor } from "../../test-utils";

function FileListWrapper() {
  // biome-ignore lint/correctness/noUnusedVariables: ESLint to Biome legacy ignore
  const [listVisible, setListVisible] = useState(true);
  const [_, setSelectedFile] = useState(false);
  return (
    <FileList
      authToken={props.authToken}
      filesUrl={props.filesUrl}
      listVisible={listVisible}
      setSelectedFile={setSelectedFile}
    />
  );
}

describe("<FileList />", () => {
  it("returns a loading state", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: ["hello", "world"] }));

    render(<FileListWrapper />);

    await waitFor(() => expect(screen.getByText("Loading…")).toBeVisible());
  });

  it("returns error state for network error", async () => {
    console.error = vi.fn();

    fetch.mockReject(new Error("Failed to connect"));

    render(<FileListWrapper />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load files")).toBeVisible(),
    );
  });

  it("returns a file list", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });
  });

  it("updates the history with the clicked file", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    await user.click(screen.queryAllByRole("link")[0]);

    expect(history.location.pathname).toBe(`/${csvFile.name}`);
  });

  it("doesn't update if the clicked file is already showing", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    history.replace("/");
    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    await user.click(screen.getByText(csvFile.shortName));
    expect(history.location.pathname).toBe(`/${csvFile.name}`);

    await user.click(screen.getByText(csvFile.shortName));
    await expect(history.location.pathname).toBe(`/${csvFile.name}`);
    expect(history.index).toBe(2);

    await user.click(screen.getByText(csvFile.shortName));
    expect(history.location.pathname).toBe(`/${csvFile.name}`);
    expect(history.index).toBe(2);
  });

  it("sorts the files by date or file name order", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    history.replace("/");
    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    user.selectOptions(screen.getByRole("combobox"), "Created date");

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        htmlFile.shortName,
      );
      expect(screen.queryAllByRole("listitem")[3].textContent).toBe(
        csvFile.shortName,
      );
    });

    user.selectOptions(screen.getByRole("combobox"), "File name");

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        csvFile.shortName,
      );
      expect(screen.queryAllByRole("listitem")[3].textContent).toBe(
        htmlFile.shortName,
      );
    });
  });
});
