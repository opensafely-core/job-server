import userEvent from "@testing-library/user-event";
import React from "react";
import Button from "../../../components/Button/Button";
import { render, screen } from "../../test-utils";

describe("<Button />", () => {
  const props = {
    isLoading: false,
    onClickFn: () => null,
    text: {
      default: "Default",
      loading: "Loading",
    },
  };

  it("shows the default state", () => {
    render(<Button {...props} isLoading={false} />);

    expect(screen.getByRole("button")).toBeEnabled();
    expect(screen.getByRole("button")).toHaveTextContent(props.text.default);
  });

  it("shows the loading state", () => {
    render(<Button {...props} isLoading />);

    expect(screen.getByRole("button")).toBeDisabled();
    expect(screen.getByRole("button")).toHaveTextContent(props.text.loading);
  });

  it("triggers the on click function", () => {
    const mockFn = jest.fn();

    render(<Button {...props} isLoading={false} onClickFn={mockFn} />);

    userEvent.click(screen.getByRole("button"));

    expect(mockFn).toBeCalledTimes(1);
  });
});
