import userEvent from "@testing-library/user-event";
import React from "react";
import toast from "react-hot-toast";
import { afterEach, describe, expect, it } from "vitest";
import Toast from "../../../components/Toast/Toast";
import { act, render, screen, waitFor } from "../../test-utils";

describe("<Toast />", () => {
  afterEach(() => {
    act(() => {
      toast.remove();
    });
  });

  it("displays and dismisses the default toast", async () => {
    const user = userEvent.setup();
    const str = "This is a notification";
    toast(str);
    render(<Toast />);

    expect(screen.getByRole("status").textContent).toBe(str);
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => {
      expect(screen.queryByText(str)).not.toBeInTheDocument();
    });
  });

  it("displays and dismisses the danger toast", async () => {
    const user = userEvent.setup();
    const str = "This is an error";
    toast.error(str);
    render(<Toast type="error" />);

    expect(screen.getByRole("status").textContent).toBe(str);
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => {
      expect(screen.queryByText(str)).not.toBeInTheDocument();
    });
  });

  it("displays and dismisses the success toast", async () => {
    const user = userEvent.setup();
    const str = "This is a success";
    toast.success(str);
    render(<Toast type="success" />);

    expect(screen.getByRole("status").textContent).toBe(str);
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => {
      expect(screen.queryByText(str)).not.toBeInTheDocument();
    });
  });
});
