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

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    expect(
      screen.getByRole("searchbox", { name: "Find a file…" }),
    ).toBeVisible();
  });

  it("shows and hides the file list", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<App {...props} />);

    window.innerWidth = 500;
    window.innerHeight = 500;
    window.dispatchEvent(new Event("resize"));

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName,
      );
    });

    expect(screen.getByRole("button").textContent).toEqual("Hide file list");
    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("button").textContent).toEqual("Show file list");
  });

  it("shows prepare button", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<App {...props} prepareUrl={prepareUrl} />);
    expect(
      screen.getByRole("button", { name: "Create a draft publication" }),
    ).toBeVisible();
  });

  it("shows publish button", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));
    render(<App {...props} publishUrl={publishUrl} />);
    expect(
      screen.getByRole("button", { name: "Create a public published output" }),
    ).toBeVisible();
  });

  it("shows the Viewer if a file is selected", async () => {
    fetch.mockResponseOnce(JSON.stringify({ files: fileList }));

    const user = userEvent.setup();
    render(<App {...props} />);

    await screen.findByText(csvFile.shortName);
    fetch.mockResponseOnce("hello,world");
    await user.click(screen.queryAllByRole("link")[0]);

    await waitFor(() => {
      expect(screen.getByText("Last modified at:")).toBeVisible();
      expect(screen.getByText("hello")).toBeVisible();
      expect(screen.getByText("world")).toBeVisible();
    });
  });
});
