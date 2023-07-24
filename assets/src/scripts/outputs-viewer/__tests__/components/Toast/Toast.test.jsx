import userEvent from "@testing-library/user-event";
import React from "react";
import toast from "react-hot-toast";
import { afterEach, describe, expect, it, vi } from "vitest";
import Toast from "../../../components/Toast/Toast";
import { render, screen, act } from "../../test-utils";

describe("<Toast />", () => {
  afterEach(() => {
    act(() => {
      toast.remove();
    });
  });

  it("displays the default toast", async () => {
    toast("This is a notification");
    render(<Toast />);

    expect(screen.getByRole("status").textContent).toBe(
      "This is a notification",
    );
    expect(
      screen.getByRole("button").classList.contains("btn-outline-secondary"),
    ).toBe(true);
  });

  it("displays the danger toast", async () => {
    toast.error("This is an error");
    render(<Toast type="error" />);

    expect(screen.getByRole("status").textContent).toBe("This is an error");
    expect(
      screen.getByRole("button").classList.contains("btn-outline-danger"),
    ).toBe(true);
  });

  it("displays the success toast", async () => {
    toast.success("This is a success");
    render(<Toast type="success" />);

    expect(screen.getByRole("status").textContent).toBe("This is a success");
    expect(
      screen.getByRole("button").classList.contains("btn-outline-success"),
    ).toBe(true);
  });

  it("dismisses the toast", async () => {
    const user = userEvent.setup();

    toast("This is a notification");
    render(<Toast />);

    vi.spyOn(toast, "dismiss").mockImplementation();

    expect(screen.getByRole("status").textContent).toBe(
      "This is a notification",
    );
    expect(
      screen.getByRole("button").classList.contains("btn-outline-secondary"),
    ).toBe(true);

    await user.click(screen.getByRole("button"));
    expect(toast.dismiss).toHaveBeenCalledTimes(1);
  });
});
