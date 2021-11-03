import userEvent from "@testing-library/user-event";
import React from "react";
import App from "../App";
import { server, rest } from "./__mocks__/server";
import { fileList } from "./helpers/files";
import { render, screen, waitFor } from "./test-utils";

describe("<App />", () => {
  it("returns the file list", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName
      );
    });

    expect(
      screen.getByRole("searchbox", { name: "Find a file…" })
    ).toBeVisible();
  });

  it("shows and hides the file list", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    render(<App />);

    window.resizeTo(500, 500);

    await waitFor(() => {
      expect(screen.queryAllByRole("listitem").length).toBe(fileList.length);
      expect(screen.queryAllByRole("listitem")[0].textContent).toBe(
        fileList[0].shortName
      );
    });

    expect(screen.getByRole("button").textContent).toEqual("Hide file list");
    userEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button").textContent).toEqual("Show file list");
  });

  it("shows publish button", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    render(<App />, {}, { publishUrl: "http://localhost" });
    expect(
      screen.getByRole("button", { name: "Confirm Publish?" })
    ).toBeVisible();
  });

  it("shows prepare button", async () => {
    server.use(
      rest.get(`http://localhost/`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ files: fileList }))
      )
    );

    render(<App />, {}, { prepareUrl: "http://localhost" });
    expect(screen.getByRole("button", { name: "Publish" })).toBeVisible();
  });
});
