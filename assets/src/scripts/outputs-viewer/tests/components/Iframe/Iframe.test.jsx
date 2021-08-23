import React from "react";
import Iframe from "../../../components/Iframe/Iframe";
import useStore from "../../../stores/use-store";
import { htmlExample, htmlFile } from "../../helpers/files";
import { render } from "../../test-utils";

describe("<Iframe />", () => {
  beforeEach(() => {
    useStore.setState((state) => ({
      ...state,
      file: htmlFile,
    }));
  });

  it("displays the iFrame data", async () => {
    const { container } = render(<Iframe data={htmlExample} />);
    const iframe = container.querySelector("iframe");

    expect(iframe.getAttribute("srcDoc")).toBe(htmlExample);
    expect(iframe.getAttribute("src")).toBe(htmlFile.url);
    expect(iframe.getAttribute("title")).toBe(htmlFile.name);
  });

  it("shows the iFrame at the correct height for small screens", async () => {
    window.resizeTo(500, 500);

    const { container } = render(<Iframe data={htmlExample} />);
    const iframe = container.querySelector("iframe");

    expect(iframe.getAttribute("height")).toBe(`1000`);
  });

  it("shows the iFrame at the correct height for large screens", async () => {
    window.resizeTo(1200, 1200);

    const { container } = render(<Iframe data={htmlExample} />);
    const iframe = container.querySelector("iframe");

    expect(iframe.getAttribute("height")).toBe(`${1200 - 17 - 40}`);
  });
});
