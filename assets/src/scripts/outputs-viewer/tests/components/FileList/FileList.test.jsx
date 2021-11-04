/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React, { useState } from "react";
import FileList from "../../../components/FileList/FileList";
import { rest, server } from "../../__mocks__/server";
import { csvFile, fileList, pngFile } from "../../helpers/files";
import { render, screen, waitFor, history } from "../../test-utils";

describe("<FileList />", () => {
  const FileListWrapper = () => {
    const [listVisible, setListVisible] = useState(false);
    return (
      <FileList listVisible={listVisible} setListVisible={setListVisible} />
    );
  };

  it("returns a loading state", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json({ files: ["hello", "world"] }))
      )
    );

    render(<FileListWrapper />);

    await waitFor(() => expect(screen.getByText("Loading…")).toBeVisible());
  });

  it("returns error state for network error", async () => {
    console.error = jest.fn();

    server.use(
      rest.get(`http://localhost/`, (req, res) =>
        res.networkError("Failed to connect")
      )
    );

    render(<FileListWrapper />);

    await waitFor(() =>
      expect(screen.getByText("Error: Unable to load files")).toBeVisible()
    );
  });

  it("returns a file list", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName
      );
    });
  });

  it("updates the history with the clicked file", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName
      );
    });

    userEvent.click(screen.queryAllByRole("link")[0]);

    expect(history.location.pathname).toBe(`/${csvFile.name}`);
  });

  it("doesn't update if the click file is already showing", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName
      );
    });
    userEvent.click(screen.queryAllByRole("link")[0]);

    expect(history.location.pathname).toBe(`/${csvFile.name}`);

    userEvent.click(screen.queryAllByRole("link")[1]);
    expect(history.location.pathname).toBe(`/${pngFile.name}`);
    expect(history.index).toBe(2);

    userEvent.click(screen.queryAllByRole("link")[1]);
    expect(history.location.pathname).toBe(`/${pngFile.name}`);
    expect(history.index).toBe(2);
  });

  it("sets the FileList height", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    const { container } = render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName
      );
    });

    const fixedSizeList = container.querySelector(".card > div");
    expect(window.getComputedStyle(fixedSizeList, null).height).toBe("738px");

    window.resizeTo(500, 500);

    await waitFor(() =>
      expect(window.getComputedStyle(fixedSizeList, null).height).toBe("570px")
    );
  });

  it("adds 17px to list height for horizontal scrollbar", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(
          ctx.status(200),
          ctx.json({
            files: [
              csvFile,
              {
                ...pngFile,
                shortName: "thisIsAReallyLongNameToAddAHorizontalScrollbar",
              },
            ],
          })
        )
      )
    );

    const { container } = render(<FileListWrapper />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(2);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        csvFile.shortName
      );
    });

    window.resizeTo(500, 500);
    const fixedSizeList = container.querySelector(".card > div");
    jest
      .spyOn(fixedSizeList, "clientWidth", "get")
      .mockImplementation(() => 100);
    jest
      .spyOn(fixedSizeList, "scrollWidth", "get")
      .mockImplementation(() => 1000);

    await waitFor(() =>
      expect(window.getComputedStyle(fixedSizeList, null).height).toBe("553px")
    );
  });
});
