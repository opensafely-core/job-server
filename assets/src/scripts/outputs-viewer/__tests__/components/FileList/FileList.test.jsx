/* eslint-disable no-console, no-unused-vars, react/prop-types */
import userEvent from "@testing-library/user-event";
import React, { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import FileList from "../../../components/FileList/FileList";
import { csvFile, fileList, htmlFile } from "../../helpers/files";
import props from "../../helpers/props";
import { history, render, screen, waitFor } from "../../test-utils";

function FileListWrapper() {
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

    expect(await screen.findByText("Loading…")).toBeVisible();
  });

  it("returns error state for network error", async () => {
    console.error = vi.fn();
    fetch.mockReject(new Error("Failed to connect"));

    render(<FileListWrapper />);

    expect(await screen.findByText("Unable to load files")).toBeVisible();
  });

  it("returns a file list", () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<FileListWrapper />);

    waitFor(() => {
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

    user.click(screen.getByRole("link", { name: csvFile.shortName }));

    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
    });
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

    user.click(screen.getByRole("link", { name: csvFile.shortName }));
    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
    });

    user.click(screen.getByRole("link", { name: csvFile.shortName }));
    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
      expect(history.index).toBe(2);
    });

    user.click(screen.getByRole("link", { name: csvFile.shortName }));
    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
      expect(history.index).toBe(2);
    });
  });

  it("sorts the files by date or file name order", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    history.replace("/");
    render(<FileListWrapper />);

    waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    expect(await screen.findByRole("combobox")).toBeVisible();

    waitFor(() => {
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        htmlFile.shortName,
      );
      expect(screen.queryAllByRole("listitem")[3].textContent).toBe(
        csvFile.shortName,
      );
    });

    user.selectOptions(screen.getByRole("combobox"), "File name");

    waitFor(() => {
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        csvFile.shortName,
      );
      expect(screen.queryAllByRole("listitem")[3].textContent).toBe(
        htmlFile.shortName,
      );
    });
  });
});
