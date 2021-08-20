import React from "react";
import Text from "../../../components/Text/Text";
import { render, screen } from "../../test-utils";

describe("<Text />", () => {
  it("show text file", async () => {
    render(<Text data="Text string" />);

    expect(screen.getByText("Text string")).toBeVisible();
  });
});
