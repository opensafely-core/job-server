/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React from "react";
import PublishButton from "../../../components/Button/PublishButton";
import * as toast from "../../../utils/toast";
import { server, rest } from "../../__mocks__/server";
import props, { publishUrl } from "../../helpers/props";
import { render, screen, waitFor } from "../../test-utils";

describe("<PublishButton />", () => {
  const mockResponse = jest.fn();
  const { csrfToken } = props;

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
    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent("Publish");
  });

  it("triggers a mutation on click", async () => {
    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

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
      rest.post(publishUrl, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);

        return res(ctx.status(403), ctx.json({ detail: "Invalid user token" }));
      })
    );

    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Confirming…")
    );
    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error: Invalid user token",
        publishUrl,
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
      rest.post(publishUrl, (req, res, ctx) => {
        // eslint-disable-next-line no-underscore-dangle
        expect(req.headers._headers["x-csrftoken"]).toBe(csrfToken);

        return res(ctx.status(500), ctx.json({}));
      })
    );

    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    userEvent.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Confirming…")
    );
    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error",
        publishUrl,
        toastId: "PublishButton",
        url: "http://localhost/",
      })
    );
  });
});
