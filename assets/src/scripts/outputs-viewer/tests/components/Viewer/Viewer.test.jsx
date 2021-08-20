/* eslint-disable no-console */
import React from "react";
import Viewer from "../../../components/Viewer/Viewer";
import useStore from "../../../stores/use-store";
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
  beforeEach(() => {
    useStore.setState((state) => ({
      ...state,
      file: htmlFile,
    }));
  });

  it("returns null if no file URL", async () => {
    useStore.setState((state) => ({
      ...state,
      file: blankFile,
    }));

    const { container } = render(<Viewer />);
    expect(container).toBeEmptyDOMElement();
  });

  it("returns a loading state", async () => {
    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(htmlExample))
      )
    );

    render(<Viewer />);
    await waitFor(() => expect(screen.getByText("Loading...")).toBeVisible());
  });

  it("returns <NoPreview /> for network error", async () => {
    console.error = jest.fn();

    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res) =>
        res.networkError("Failed to connect")
      )
    );

    render(<Viewer />);
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

    render(<Viewer />);
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <NoPreview /> for invalid file type", async () => {
    console.error = jest.fn();

    useStore.setState((state) => ({
      ...state,
      file: jsFile,
    }));

    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json())
      )
    );

    render(<Viewer />);
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

    render(<Viewer />);
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <NoPreview /> for too large CSV", async () => {
    console.error = jest.fn();

    useStore.setState((state) => ({
      ...state,
      file: { ...csvFile, size: 5000001 },
    }));

    server.use(
      rest.get(`http://localhost${csvFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.body(csvExample))
      )
    );

    render(<Viewer />);
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <NoPreview /> for failed PNG", async () => {
    useStore.setState((state) => ({
      ...state,
      file: pngFile,
    }));

    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res) =>
        res.networkError("Failed to connect")
      )
    );

    render(<Viewer />);
    await waitFor(() =>
      expect(
        screen.getByText("We cannot show a preview of this file.")
      ).toBeVisible()
    );
  });

  it("returns <Table /> for CSV", async () => {
    useStore.setState((state) => ({
      ...state,
      file: csvFile,
    }));

    server.use(
      rest.get(`http://localhost${csvFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(csvExample))
      )
    );

    render(<Viewer />);
    await waitFor(() => expect(screen.getByRole("table")).toBeVisible());
  });

  it("returns <Iframe /> for HTML", async () => {
    useStore.setState((state) => ({
      ...state,
      file: htmlFile,
    }));

    server.use(
      rest.get(`http://localhost${htmlFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(htmlExample))
      )
    );

    const { container } = render(<Viewer />);

    await waitFor(() => {
      const iframe = container.querySelector("iframe");
      return expect(iframe.getAttribute("srcDoc")).toBe(htmlExample);
    });
  });

  it("returns <Image /> for PNG", async () => {
    useStore.setState((state) => ({
      ...state,
      file: pngFile,
    }));

    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res, ctx) =>
        res.once(
          ctx.set("Content-Type", "image/png"),
          ctx.status(200),
          ctx.body({ Blob: pngExample })
        )
      )
    );

    render(<Viewer />);

    await waitFor(() => expect(screen.getByRole("img").src).toBe(pngExample));
  });

  it("returns <Text /> for TXT", async () => {
    useStore.setState((state) => ({
      ...state,
      file: txtFile,
    }));

    server.use(
      rest.get(`http://localhost${txtFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(txtExample))
      )
    );

    render(<Viewer />);

    await waitFor(() => expect(screen.getByText(txtExample)).toBeVisible());
  });

  it("returns <Text /> for JSON", async () => {
    useStore.setState((state) => ({
      ...state,
      file: jsonFile,
    }));

    server.use(
      rest.get(`http://localhost${jsonFile.url}`, (req, res, ctx) =>
        res.once(ctx.status(200), ctx.json(jsonExample))
      )
    );

    render(<Viewer />);

    await waitFor(() =>
      expect(screen.getByText(JSON.stringify(jsonExample))).toBeVisible()
    );
  });
});
