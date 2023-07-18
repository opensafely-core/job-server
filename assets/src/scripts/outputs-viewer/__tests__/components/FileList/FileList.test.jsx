/* eslint-disable no-console, no-unused-vars, react/prop-types */
import userEvent from "@testing-library/user-event";
import React, { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import FileList from "../../../components/FileList/FileList";
import { rest, server } from "../../__mocks__/server";
import { csvFile, fileList, pngFile } from "../../helpers/files";
import props from "../../helpers/props";
import { render, screen, waitFor, history } from "../../test-utils";

function FileListWrapper() {
  const [listVisible, setListVisible] = useState(false);
  const [_, setSelectedFile] = useState(false);
  return (
    <FileList
      authToken={props.authToken}
      filesUrl={props.filesUrl}
      listVisible={listVisible}
      setListVisible={setListVisible}
      setSelectedFile={setSelectedFile}
    />
  );
}

describe("<FileList />", () => {
  it("returns a loading state", async () => {
    server.use(
      rest.get(props.filesUrl, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json({ files: ["hello", "world"] })),
      ),
    );

    render(<FileListWrapper />);

    await waitFor(() => expect(screen.getByText("Loading…")).toBeVisible());
  });

  it("returns error state for network error", async () => {
    console.error = vi.fn();

    server.use(
      rest.get(props.filesUrl, (req, res) =>
        res.networkError("Failed to connect"),
      ),
    );

    render(<FileListWrapper />);

    await waitFor(() =>
      expect(screen.getByText("Error: Unable to load files")).toBeVisible(),
    );
  });

  it("returns a file list", async () => {
    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].name,
      );
    });
  });

  it("updates the history with the clicked file", async () => {
    const user = userEvent.setup();
    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].name,
      );
    });

    await user.click(screen.queryAllByRole("link")[0]);

    expect(history.location.pathname).toBe(`/${csvFile.name}`);
  });

  it("doesn't update if the click file is already showing", async () => {
    const user = userEvent.setup();
    history.replace("/");
    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].name,
      );
    });

    await user.click(screen.getByText(csvFile.name));
    expect(history.location.pathname).toBe(`/${csvFile.name}`);

    await user.click(screen.getByText(csvFile.name));
    await expect(history.location.pathname).toBe(`/${csvFile.name}`);
    expect(history.index).toBe(2);

    await user.click(screen.getByText(csvFile.name));
    expect(history.location.pathname).toBe(`/${csvFile.name}`);
    expect(history.index).toBe(2);
  });

  it("sets the FileList height", async () => {
    const { container } = render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].name,
      );
    });

    const fixedSizeList = container.querySelector(".card > div");
    expect(window.getComputedStyle(fixedSizeList, null).height).toBe("738px");

    window.resizeTo(500, 500);

    await waitFor(() =>
      expect(window.getComputedStyle(fixedSizeList, null).height).toBe("570px"),
    );
  });

  it("adds 17px to list height for horizontal scrollbar", async () => {
    server.use(
      rest.get(props.filesUrl, (req, res, ctx) =>
        res(
          ctx.status(200),
          ctx.json({
            files: [
              csvFile,
              {
                ...pngFile,
                name: "thisIsAReallyLongNameToAddAHorizontalScrollbar",
              },
            ],
          }),
        ),
      ),
    );

    const { container } = render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(2);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        csvFile.name,
      );
    });

    window.resizeTo(500, 500);
    const fixedSizeList = container.querySelector(".card > div");
    vi.spyOn(fixedSizeList, "clientWidth", "get").mockImplementation(() => 100);
    vi.spyOn(fixedSizeList, "scrollWidth", "get").mockImplementation(
      () => 1000,
    );

    await waitFor(() =>
      expect(window.getComputedStyle(fixedSizeList, null).height).toBe("553px"),
    );
  });
});
