/* eslint-disable no-console */
import React from "react";
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
import { screen, render, waitFor } from "../../test-utils";

describe("<Viewer />", () => {
  it("returns null if no file URL", async () => {
    const { container } = render(<Viewer />, {}, { file: blankFile });
    expect(container).toBeEmptyDOMElement();
  });

  it("returns a loading state", async () => {
    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(htmlExample))
      )
    );

    render(<Viewer />, {}, { file: htmlFile });
    await waitFor(() => expect(screen.getByText("Loading...")).toBeVisible());
  });

  it("returns <NoPreview /> for network error", async () => {
    console.error = jest.fn();

    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res) =>
        res.networkError("Failed to connect")
      )
    );

    render(<Viewer />, {}, { file: htmlFile });
    await waitFor(() =>
      expect(screen.getByText("Error: Network Error")).toBeVisible()
    );
  });

  it("returns <NoPreview /> for no data", async () => {
    console.error = jest.fn();

    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json())
      )
    );

    render(<Viewer />, {}, { file: htmlFile });
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <NoPreview /> for invalid file type", async () => {
    console.error = jest.fn();

    server.use(
      rest.get(`http://localhost${jsFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json())
      )
    );

    render(<Viewer />, {}, { file: jsFile });
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <NoPreview /> for empty data", async () => {
    console.error = jest.fn();

    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.body({}))
      )
    );

    render(<Viewer />, {}, { file: htmlFile });
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <NoPreview /> for too large CSV", async () => {
    console.error = jest.fn();

    server.use(
      rest.get(`http://localhost${csvFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.body(csvExample))
      )
    );

    render(<Viewer />, {}, { file: { ...csvFile, size: 5000001 } });
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <NoPreview /> for failed PNG", async () => {
    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res) =>
        res.networkError("Failed to connect")
      )
    );

    render(<Viewer />, {}, { file: pngFile });
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <Table /> for CSV", async () => {
    server.use(
      rest.get(`http://localhost${csvFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(csvExample))
      )
    );

    render(<Viewer />, {}, { file: csvFile });
    await waitFor(() => expect(screen.getByRole("table")).toBeVisible());
  });

  it("returns <Iframe /> for HTML", async () => {
    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(htmlExample))
      )
    );

    const { container } = render(<Viewer />, {}, { file: htmlFile });

    await waitFor(() => {
      const iframe = container.querySelector("iframe");
      return expect(iframe.getAttribute("srcDoc")).toBe(htmlExample);
    });
  });

  it("returns <Image /> for PNG", async () => {
    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res, ctx) =>
        res.once(
          ctx.set("Content-Type", "image/png"),
          ctx.status(200),
          ctx.body({ Blob: pngExample })
        )
      )
    );

    render(<Viewer />, {}, { file: pngFile });

    await waitFor(() =>
      expect(screen.getByRole("img").src).toBe(
        `data:image/png;base64,W29iamVjdCBPYmplY3Rd`
      )
    );
  });

  it("returns <Text /> for TXT", async () => {
    server.use(
      rest.get(`http://localhost${txtFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(txtExample))
      )
    );

    render(<Viewer />, {}, { file: txtFile });

    await waitFor(() => expect(screen.getByText(txtExample)).toBeVisible());
  });

  it("returns <Text /> for JSON", async () => {
    server.use(
      rest.get(`http://localhost${jsonFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(jsonExample))
      )
    );

    render(<Viewer />, {}, { file: jsonFile });

    await waitFor(() =>
      expect(screen.getByText(JSON.stringify(jsonExample))).toBeVisible()
    );
  });
});
