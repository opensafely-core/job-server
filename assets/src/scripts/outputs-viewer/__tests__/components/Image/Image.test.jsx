import React from "react";
import { describe, expect, it } from "vitest";
import Image from "../../../components/Image/Image";
import { pngExample } from "../../helpers/files";
import { render, screen } from "../../test-utils";

describe("<Image />", () => {
  it("shows an image if a data blob is passed", async () => {
    render(<Image data={pngExample} />);

    expect(screen.getByRole("img").src).toBe(pngExample);
  });
});
