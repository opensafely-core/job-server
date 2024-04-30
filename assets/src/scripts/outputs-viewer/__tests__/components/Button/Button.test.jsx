import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import Button from "../../../components/Button/Button";

describe("<Button />", () => {
  it("triggers function on click", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<Button onClick={handleClick}>Primary button</Button>);
    await user.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalled();
  });
});
