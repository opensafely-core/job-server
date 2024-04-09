/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import PublishButton from "../../../components/Button/PublishButton";
import * as toast from "../../../utils/toast";
import props, { publishUrl } from "../../helpers/props";
import { render, screen, waitFor } from "../../test-utils";

describe("<PublishButton />", () => {
  const { csrfToken } = props;

  it("shows the button", async () => {
    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a public published output",
    );

    expect(
      await screen.findByRole("button", {
        name: "Create a public published output",
      }),
    ).toBeVisible();
  });

  it("triggers a mutation on click", async () => {
    const user = userEvent.setup();
    fetch.mockResponseOnce(
      () =>
        new Promise((resolve) =>
          // eslint-disable-next-line no-promise-executor-return
          setTimeout(() => resolve({ body: "ok" }), 100),
        ),
    );

    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    const publicBtn = await screen.findByRole("button", {
      name: "Create a public published output",
    });
    expect(publicBtn).toBeVisible();
    user.click(publicBtn);

    expect(
      await screen.findByRole("button", { name: "Creating…" }),
    ).toBeVisible();

    waitFor(() => expect(fetch.requests().length).toEqual(1));
  });

  it("show the JSON error message", async () => {
    const user = userEvent.setup();
    const toastError = vi.fn();
    console.error = vi.fn();

    vi.spyOn(toast, "toastError").mockImplementation(toastError);

    fetch.mockRejectOnce(new Error("Invalid user token"));

    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    const publicBtn = await screen.findByRole("button", {
      name: "Create a public published output",
    });
    expect(publicBtn).toBeVisible();
    user.click(publicBtn);

    waitFor(() =>
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

    fetch.mockRejectOnce(new Error());

    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    const publicBtn = await screen.findByRole("button", {
      name: "Create a public published output",
    });
    expect(publicBtn).toBeVisible();
    user.click(publicBtn);

    waitFor(() =>
      expect(toastError).toHaveBeenCalledWith({
        message: "Error",
        publishUrl,
        toastId: "PublishButton",
        url: "http://localhost:3000/",
      }),
    );
  });
});
