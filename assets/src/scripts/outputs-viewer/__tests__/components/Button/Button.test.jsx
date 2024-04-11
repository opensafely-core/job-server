import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import Button from "../../../components/Button/Button";

describe("<Button />", () => {
  it("triggers function on click", async () => {
    const user = userEvent.setup();
    vi.spyOn(Button.defaultProps, "onClick");

    render(<Button>Primary button</Button>);
    await user.click(screen.getByRole("button"));
    expect(Button.defaultProps.onClick).toHaveBeenCalled();
  });
});
