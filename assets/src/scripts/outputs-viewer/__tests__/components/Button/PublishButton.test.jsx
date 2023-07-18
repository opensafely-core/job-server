/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";
import PublishButton from "../../../components/Button/PublishButton";
import * as toast from "../../../utils/toast";
import { server, rest } from "../../__mocks__/server";
import props, { publishUrl } from "../../helpers/props";
import { render, screen, waitFor } from "../../test-utils";

describe("<PublishButton />", () => {
  const mockResponse = vi.fn();
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
    vi.resetAllMocks();
  });

  it("shows the button", () => {
    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent("Publish");
  });

  it("triggers a mutation on click", async () => {
    const user = userEvent.setup();
    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    await user.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Confirming…"),
    );
    await waitFor(() => expect(mockResponse).toHaveBeenCalledTimes(1));
  });

  it("show the JSON error message", async () => {
    const user = userEvent.setup();
    const toastError = vi.fn();
    console.error = vi.fn();

    vi.spyOn(toast, "toastError").mockImplementation(toastError);

    server.use(
      rest.post(publishUrl, (req, res, ctx) =>
        res(ctx.status(403), ctx.json({ detail: "Invalid user token" })),
      ),
    );

    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    await user.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error: Invalid user token",
        publishUrl,
        toastId: "PublishButton",
        url: "http://localhost:3000/",
      }),
    );
  });

  it("show the server error message", async () => {
    const user = userEvent.setup();
    const toastError = vi.fn();
    console.error = vi.fn();

    vi.spyOn(toast, "toastError").mockImplementation(toastError);

    server.use(
      rest.post(publishUrl, (req, res, ctx) =>
        res(ctx.status(500), ctx.json({})),
      ),
    );

    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent("Confirm Publish?");

    await user.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error",
        publishUrl,
        toastId: "PublishButton",
        url: "http://localhost:3000/",
      }),
    );
  });
});
