import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it } from "vitest";
import App from "../App";
import { fileList } from "./helpers/files";
import props, { prepareUrl, publishUrl } from "./helpers/props";
import { render, screen, waitFor } from "./test-utils";

describe("<App />", () => {
  it("returns the file list", async () => {
    render(<App {...props} />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].name,
      );
    });

    expect(
      screen.getByRole("searchbox", { name: "Find a file…" }),
    ).toBeVisible();
  });

  it("shows and hides the file list", async () => {
    render(<App {...props} />);

    window.resizeTo(500, 500);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].name,
      );
    });

    expect(screen.getByRole("button").textContent).toEqual("Hide file list");
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button").textContent).toEqual("Show file list");
  });

  it("shows prepare button", async () => {
    render(<App {...props} prepareUrl={prepareUrl} />);
    expect(screen.getByRole("button", { name: "Publish" })).toBeVisible();
  });

  it("shows publish button", async () => {
    render(<App {...props} publishUrl={publishUrl} />);
    expect(
      screen.getByRole("button", { name: "Confirm Publish?" }),
    ).toBeVisible();
  });

  it("shows the Viewer if a file is selected", async () => {
    const user = userEvent.setup();
    render(<App {...props} />);

    await user.click(screen.queryAllByRole("link")[0]);
    await waitFor(() => {
      expect(screen.getByText("Last modified at:")).toBeVisible();
      expect(screen.getByText("hello")).toBeVisible();
      expect(screen.getByText("world")).toBeVisible();
    });
  });
});
