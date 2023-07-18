/* eslint-disable no-console */
import React from "react";
import { describe, expect, it, vi } from "vitest";
import Viewer from "../../../components/Viewer/Viewer";
import { server, rest } from "../../__mocks__/server";
import {
  blankFile,
  csvExample,
  csvFile,
  htmlExample,
  htmlFile,
  pngFile,
  jsFile,
  pngExample,
  txtFile,
  txtExample,
  jsonFile,
  jsonExample,
} from "../../helpers/files";
import props, { uuid } from "../../helpers/props";
import { screen, render, waitFor } from "../../test-utils";

describe("<Viewer />", () => {
  it("returns a loading state", async () => {
    server.use(
      rest.get(`http://localhost:3000${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(htmlExample)),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={blankFile.name}
        fileSize={blankFile.size}
        fileUrl={blankFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() => expect(screen.getByText("Loading...")).toBeVisible());
  });

  it("returns <NoPreview /> for network error", async () => {
    console.error = vi.fn();
    server.use(
      rest.get(`http://localhost:3000${htmlFile.url}`, (req, res) =>
        res.networkError("Failed to connect"),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={htmlFile.name}
        fileSize={htmlFile.size}
        fileUrl={htmlFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText("Error: Failed to fetch")).toBeVisible(),
    );
  });

  it("returns <NoPreview /> for no data", async () => {
    console.error = vi.fn();
    server.use(
      rest.get(`http://localhost:3000${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json()),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={htmlFile.name}
        fileSize={htmlFile.size}
        fileUrl={htmlFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file."),
      ).toBeVisible(),
    );
  });

  it("returns <NoPreview /> for invalid file type", async () => {
    console.error = vi.fn();
    server.use(
      rest.get(`http://localhost:3000${jsFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json({})),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={jsFile.name}
        fileSize={jsFile.size}
        fileUrl={jsFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file."),
      ).toBeVisible(),
    );
  });

  it("returns <NoPreview /> for empty data", async () => {
    console.error = vi.fn();
    server.use(
      rest.get(`http://localhost:3000${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.body()),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={htmlFile.name}
        fileSize={htmlFile.size}
        fileUrl={htmlFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file."),
      ).toBeVisible(),
    );
  });

  it("returns <NoPreview /> for too large CSV", async () => {
    console.error = vi.fn();
    server.use(
      rest.get(`http://localhost:3000${csvFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.body(csvExample)),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={csvFile.name}
        fileSize={5000001}
        fileUrl={csvFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file."),
      ).toBeVisible(),
    );
  });

  it("returns <NoPreview /> for failed PNG", async () => {
    server.use(
      rest.get(`http://localhost:3000${pngFile.url}`, (req, res) =>
        res.networkError("Failed to connect"),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={pngFile.name}
        fileSize={pngFile.size}
        fileUrl={pngFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file."),
      ).toBeVisible(),
    );
  });

  it("returns <Table /> for CSV", async () => {
    server.use(
      rest.get(`http://localhost:3000${csvFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(csvExample)),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={csvFile.name}
        fileSize={csvFile.size}
        fileUrl={csvFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() => expect(screen.getByRole("table")).toBeVisible());
  });

  it("returns <Iframe /> for HTML", async () => {
    server.use(
      rest.get(`http://localhost:3000${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(htmlExample)),
      ),
    );
    const { container } = render(
      <Viewer
        authToken={props.authToken}
        fileName={htmlFile.name}
        fileSize={htmlFile.size}
        fileUrl={htmlFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() => {
      const iframe = container.querySelector("iframe");
      return expect(iframe.getAttribute("srcDoc")).toContain(
        JSON.stringify(htmlExample),
      );
    });
  });

  it("returns <Image /> for PNG", async () => {
    server.use(
      rest.get(`http://localhost:3000${pngFile.url}`, (req, res, ctx) =>
        res.once(
          ctx.set("Content-Type", "image/png"),
          ctx.status(200),
          ctx.body({ Blob: pngExample }),
        ),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={pngFile.name}
        fileSize={pngFile.size}
        fileUrl={pngFile.url}
        uuid={uuid}
      />,
    );

    await waitFor(() =>
      expect(screen.getByRole("img").src).toBe(`http://localhost:3000/imgSrc`),
    );
  });

  it("returns <Text /> for TXT", async () => {
    server.use(
      rest.get(`http://localhost:3000${txtFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(txtExample)),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={txtFile.name}
        fileSize={txtFile.size}
        fileUrl={txtFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText(`"${txtExample}"`)).toBeVisible(),
    );
  });

  it("returns <Text /> for JSON", async () => {
    server.use(
      rest.get(`http://localhost:3000${jsonFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json({ ...jsonExample })),
      ),
    );
    render(
      <Viewer
        authToken={props.authToken}
        fileName={jsonFile.name}
        fileSize={jsonFile.size}
        fileUrl={jsonFile.url}
        uuid={uuid}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(JSON.stringify(jsonExample))).toBeVisible();
    });
  });
});
