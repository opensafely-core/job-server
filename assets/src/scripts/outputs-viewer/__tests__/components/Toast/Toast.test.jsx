import userEvent from "@testing-library/user-event";
import React from "react";
import { toast } from "react-toastify";
import { describe, expect, it } from "vitest";
import Toast from "../../../components/Toast/Toast";
import {
  fireEvent,
  render,
  screen,
  waitForElementToBeRemoved,
} from "../../test-utils";

describe("<Toast />", () => {
  const opts = {
    autoClose: false,
    closeOnClick: false,
    draggable: false,
    hideProgressBar: true,
    id: 123,
    pauseOnHover: false,
    position: "top-right",
    theme: "light",
  };

  it("displays and dismisses the default toast", async () => {
    const user = userEvent.setup();
    const str = "This is a notification";

    toast(str, opts);
    render(<Toast />);

    screen.getByText(str);

    await user.click(screen.getByRole("button", { name: /close/i }));
    fireEvent.animationEnd(screen.getByText(str));

    await waitForElementToBeRemoved(screen.getByText(str));
  });

  it("displays and dismisses the danger toast", async () => {
    const user = userEvent.setup();
    const str = "This is an error";

    toast.error(str, opts);
    const { container } = render(<Toast />);

    screen.getByText(str);

    expect(
      container.getElementsByClassName("Toastify__toast--error").length,
    ).toBe(1);

    await user.click(screen.getByRole("button", { name: /close/i }));
    fireEvent.animationEnd(screen.getByText(str));

    await waitForElementToBeRemoved(screen.getByText(str));
  });

  it("displays and dismisses the success toast", async () => {
    const user = userEvent.setup();
    const str = "This is a success";

    toast.success(str, opts);
    const { container } = render(<Toast />);

    screen.getByText(str);

    expect(
      container.getElementsByClassName("Toastify__toast--success").length,
    ).toBe(1);

    await user.click(screen.getByRole("button", { name: /close/i }));
    fireEvent.animationEnd(screen.getByText(str));

    await waitForElementToBeRemoved(screen.getByText(str));
  });
});
