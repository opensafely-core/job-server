/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React from "react";
import PublishButton from "../../../components/Button/PublishButton";
import * as toast from "../../../utils/toast";
import { server, rest } from "../../__mocks__/server";
import { render, screen, waitFor } from "../../test-utils";

describe("<PublishButton />", () => {
  const mockResponse = jest.fn();
  const urls = {
    publish: "http://localhost/publish",
    redirect: "http://localhost/prepare-redirect",
  };
  const csrfToken = "abc123";

  beforeEach(() => {
    /**
     * Mock window
     */
    Object.defineProperty(window, "location", {
      value: {
        reload: mockResponse,
      },
      writable: true,
    });
  });

  afterAll(() => {
    jest.resetAllMocks();
  });

  it("shows the button", () => {
    render(<PublishButton />, {}, { csrfToken, publishUrl: urls.publish });

    expect(screen.getByRole("button")).toHaveTextContent("Publish");
  });

  it("triggers a mutation on click", async () => {
    server.use(
      rest.post(urls.publish, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);

        return res(ctx.json({}));
      })
    );

    render(<PublishButton />, {}, { csrfToken, publishUrl: urls.publish });

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Confirming…")
    );
    await waitFor(() => expect(mockResponse).toHaveBeenCalledTimes(1));
  });

  it("show the JSON error message", async () => {
    const toastError = jest.fn();
    console.error = jest.fn();

    jest.spyOn(toast, "toastError").mockImplementation(toastError);

    server.use(
      rest.post(urls.publish, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);

        return res(ctx.status(403), ctx.json({ detail: "Invalid user token" }));
      })
    );

    render(<PublishButton />, {}, { csrfToken, publishUrl: urls.publish });

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Confirming…")
    );
    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Invalid user token",
        publishUrl: urls.publish,
        toastId: "PublishButton",
        url: "http://localhost/",
      })
    );
  });

  it("show the server error message", async () => {
    const toastError = jest.fn();
    console.error = jest.fn();

    jest.spyOn(toast, "toastError").mockImplementation(toastError);

    server.use(
      rest.post(urls.publish, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);

        return res(ctx.status(500));
      })
    );

    render(<PublishButton />, {}, { csrfToken, publishUrl: urls.publish });

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Confirming…")
    );
    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error: Request failed with status code 500",
        publishUrl: urls.publish,
        toastId: "PublishButton",
        url: "http://localhost/",
      })
    );
  });
});
