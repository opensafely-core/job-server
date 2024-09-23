/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React from "react";
import { ToastContainer } from "react-toastify";
import { describe, expect, it, vi } from "vitest";
import PublishButton from "../../../components/Button/PublishButton";
import props, { publishUrl } from "../../helpers/props";
import { render, screen, waitFor } from "../../test-utils";

describe("<PublishButton />", () => {
  const { csrfToken } = props;

  it("shows the button", () => {
    render(<PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />);

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a public published output",
    );
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

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a public published output",
    );

    await user.click(screen.getByRole("button"));

    expect(screen.getByRole("button")).toHaveTextContent("Creating…");

    await waitFor(() => expect(fetch.requests().length).toEqual(1));
  });

  it("show the JSON error message", async () => {
    const user = userEvent.setup();
    console.error = vi.fn();

    fetch.mockRejectOnce(new Error("Invalid user token"));

    render(
      <>
        <ToastContainer />
        <PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />
      </>,
    );

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a public published output",
    );

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Error: Invalid user token",
    );
  });

  it("show the server error message", async () => {
    const user = userEvent.setup();
    console.error = vi.fn();

    fetch.mockRejectOnce(new Error());

    render(
      <>
        <ToastContainer />
        <PublishButton csrfToken={csrfToken} publishUrl={publishUrl} />
      </>,
    );

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a public published output",
    );

    screen.debug();

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("alert")).toHaveTextContent("Error");
  });
});
