import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it } from "vitest";
import App from "../App";
import { csvFile, fileList } from "./helpers/files";
import props, { prepareUrl, publishUrl } from "./helpers/props";
import { render, screen, waitFor } from "./test-utils";

describe("<App />", () => {
  it("returns the file list", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<App {...props} />);

    waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    expect(
      await screen.findByRole("searchbox", { name: "Find a file…" }),
    ).toBeVisible();
  });

  it("shows and hides the file list", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<App {...props} />);

    window.resizeTo(500, 500);

    waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    const btn = await screen.findByRole("button", { name: "Hide file list" });
    expect(btn).toBeVisible();
    user.click(btn);
    expect(await screen.findByRole("button", { name: "Show file list" }));
  });

  it("shows prepare button", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<App {...props} prepareUrl={prepareUrl} />);
    expect(
      await screen.findByRole("button", { name: "Create a draft publication" }),
    ).toBeVisible();
  });

  it("shows publish button", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<App {...props} publishUrl={publishUrl} />);
    expect(
      await screen.findByRole("button", {
        name: "Create a public published output",
      }),
    ).toBeVisible();
  });

  it("shows the Viewer if a file is selected", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    fetch.mockResponseOnce(["hello", "world"]);

    render(<App {...props} />);

    expect(await screen.findByText(csvFile.shortName)).toBeVisible();
    user.click(await screen.findByRole("link", { name: csvFile.shortName }));

    expect(await screen.findByText("Last modified at:")).toBeVisible();
    expect(await screen.findByRole("cell", { name: "hello" })).toBeVisible();
    expect(await screen.findByRole("cell", { name: "world" })).toBeVisible();
  });
});
