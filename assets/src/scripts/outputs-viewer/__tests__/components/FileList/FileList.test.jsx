/* eslint-disable no-console, no-unused-vars, react/prop-types */
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
import { render, screen, waitFor, history } from "../../test-utils";

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

    waitFor(() => expect(screen.getByText("Loading…")).toBeVisible());
  });

  it("returns error state for network error", async () => {
    console.error = vi.fn();

    fetch.mockReject(new Error("Failed to connect"));

    render(<FileListWrapper />);

    waitFor(() =>
      expect(screen.getByText("Unable to load files")).toBeVisible(),
    );
  });

  it("returns a file list", async () => {
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

    waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    const csvLink = await screen.findByRole("link", {
      name: csvFile.shortName,
    });
    expect(csvLink).toBeVisible();
    user.click(csvLink);

    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
    });
  });

  it("doesn't update if the clicked file is already showing", async () => {
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

    const csvLink = await screen.findByRole("link", {
      name: csvFile.shortName,
    });
    expect(csvLink).toBeVisible();

    user.click(csvLink);
    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
    });

    user.click(csvLink);
    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
      expect(history.index).toBe(1);
    });

    user.click(csvLink);
    waitFor(() => {
      expect(history.location.pathname).toBe(`/${csvFile.name}`);
      expect(history.index).toBe(1);
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

    userEvent.selectOptions(
      await screen.findByRole("combobox"),
      "Created date",
    );

    waitFor(() => {
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        htmlFile.shortName,
      );
      expect(screen.queryAllByRole("listitem")[3].textContent).toBe(
        csvFile.shortName,
      );
    });

    userEvent.selectOptions(await screen.findByRole("combobox"), "File name");

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
