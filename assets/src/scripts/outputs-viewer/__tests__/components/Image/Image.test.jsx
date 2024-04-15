import React from "react";
import { describe, expect, it } from "vitest";
import Image from "../../../components/Image/Image";
import { pngExample } from "../../helpers/files";
import { render } from "../../test-utils";

describe("<Image />", () => {
  it("shows an image if a data blob is passed", async () => {
    const { container } = render(<Image data={pngExample} />);
    expect(container.querySelector("img").getAttribute("src")).toBe(pngExample);
  });
});
