/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React from "react";
import PrepareButton from "../../../components/Button/PrepareButton";
import * as useFileList from "../../../hooks/use-file-list";
import * as toast from "../../../utils/toast";
import { server, rest } from "../../__mocks__/server";
import { fileList } from "../../helpers/files";
import props, { prepareUrl } from "../../helpers/props";
import { render, screen, waitFor } from "../../test-utils";

describe("<PrepareButton />", () => {
  const urls = {
    prepare: "http://localhost/prepare",
    redirect: "http://localhost/prepare-redirect",
  };

  const { authToken, csrfToken, filesUrl } = props;

  const fileIds = ["abc1", "abc2", "abc3", "abc4"];

  beforeEach(() => {
    /**
     * Mock window
     */
    Object.defineProperty(window, "location", {
      value: {},
      writable: true,
    });
  });

  afterAll(() => {
    jest.resetAllMocks();
  });

  it("hides the element if there are no files", () => {
    jest.spyOn(useFileList, "default").mockImplementation(() => ({
      data: [],
    }));

    const { container } = render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("shows if there are files", () => {
    jest.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />
    );

    expect(screen.getByRole("button")).toHaveTextContent("Publish");
  });

  it("triggers a mutation on click", async () => {
    jest.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    server.use(
      rest.post(prepareUrl, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);
        expect(req.body.file_ids).toEqual(fileIds);

        return res(
          ctx.json({
            url: urls.redirect,
          })
        );
      })
    );

    render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />
    );

    expect(screen.getByRole("button")).toHaveTextContent("Publish");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Publishing…")
    );
    await waitFor(() => expect(window.location.href).toEqual(urls.redirect));
  });

  it("show the JSON error message", async () => {
    const toastError = jest.fn();
    console.error = jest.fn();

    jest.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    jest.spyOn(toast, "toastError").mockImplementation(toastError);

    server.use(
      rest.post(prepareUrl, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);
        expect(req.body.file_ids).toEqual(fileIds);

        return res(ctx.status(403), ctx.json({ detail: "Invalid user token" }));
      })
    );

    render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />
    );

    expect(screen.getByRole("button")).toHaveTextContent("Publish");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Publishing…")
    );
    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error: Invalid user token",
        prepareUrl,
        toastId: "PrepareButton",
        url: "http://localhost/",
      })
    );
  });

  it("show the server error message", async () => {
    const toastError = jest.fn();
    console.error = jest.fn();

    jest.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    jest.spyOn(toast, "toastError").mockImplementation(toastError);

    server.use(
      rest.post(prepareUrl, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);
        expect(req.body.file_ids).toEqual(fileIds);

        return res(ctx.status(500), ctx.json({}));
      })
    );

    render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />
    );

    expect(screen.getByRole("button")).toHaveTextContent("Publish");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Publishing…")
    );
    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error",
        prepareUrl,
        toastId: "PrepareButton",
        url: "http://localhost/",
      })
    );
  });
});
