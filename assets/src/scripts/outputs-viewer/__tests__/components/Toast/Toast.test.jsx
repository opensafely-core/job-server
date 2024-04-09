import userEvent from "@testing-library/user-event";
import React from "react";
import toast from "react-hot-toast";
import { afterEach, describe, expect, it, vi } from "vitest";
import Toast from "../../../components/Toast/Toast";
import {
  act,
  render,
  screen,
  waitForElementToBeRemoved,
} from "../../test-utils";

describe("<Toast />", () => {
  afterEach(() => {
    act(() => {
      toast.remove();
    });
    vi.resetAllMocks();
  });

  it("displays and dismisses the default toast", async () => {
    const user = userEvent.setup();
    const str = "This is a notification";
    toast(str);
    render(<Toast />);

    const toaster = await screen.findByRole("status");
    expect(toaster.textContent).toBe(str);

    user.click(screen.getByRole("button", { name: "Dismiss" }));

    waitForElementToBeRemoved(() => screen.queryByText(str));
  });

  it("displays and dismisses the danger toast", async () => {
    const user = userEvent.setup();
    const str = "This is an error";
    toast.error(str);
    render(<Toast type="error" />);

    const toaster = await screen.findByRole("status");
    expect(toaster.textContent).toBe(str);

    user.click(screen.getByRole("button", { name: "Dismiss" }));

    waitForElementToBeRemoved(() => screen.queryByText(str));
  });

  it("displays and dismisses the success toast", async () => {
    const user = userEvent.setup();
    const str = "This is a success";
    toast.success(str);
    render(<Toast type="success" />);

    const toaster = await screen.findByRole("status");
    expect(toaster.textContent).toBe(str);

    user.click(screen.getByRole("button", { name: "Dismiss" }));

    waitForElementToBeRemoved(() => screen.queryByText(str));
  });

  it("fires the dismiss event", async () => {
    vi.spyOn(toast, "dismiss").mockImplementation((id) => id);
    const user = userEvent.setup();
    const str = "This is a success";
    toast.success(str);
    render(<Toast type="success" />);

    const toaster = await screen.findByRole("status");
    expect(toaster.textContent).toBe(str);

    await user.click(screen.getByRole("button", { name: "Dismiss" }));

    expect(toast.dismiss).toHaveBeenCalledWith("4");
  });
});
