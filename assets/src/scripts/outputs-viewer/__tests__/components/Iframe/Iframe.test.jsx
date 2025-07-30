import React from "react";
import { beforeEach, describe, expect, it } from "vitest";
import Iframe from "../../../components/Iframe/Iframe";
import { htmlExample, htmlFile } from "../../helpers/files";
import { render } from "../../test-utils";

describe("<Iframe />", () => {
  it("displays the iFrame data", async () => {
    const { container } = render(
      <Iframe
        data={htmlExample}
        fileName={htmlFile.name}
        fileUrl={htmlFile.url}
      />,
    );
    const iframe = container.querySelector("iframe");

    expect(iframe.getAttribute("srcDoc")).toBe(htmlExample);
    expect(iframe.getAttribute("src")).toBe(htmlFile.url);
    expect(iframe.getAttribute("title")).toBe(htmlFile.name);
  });

  it("shows the iFrame at the correct height for small screens", () => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 500,
    });

    const { container } = render(
      <Iframe
        data={htmlExample}
        fileName={htmlFile.name}
        fileUrl={htmlFile.url}
      />,
    );
    const iframe = container.querySelector("iframe");

    expect(iframe.getAttribute("height")).toBe(`1000`);
  });

  describe("on large screens", () => {
    beforeEach(() => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 1200,
      });

      const iframeId = encodeURIComponent(htmlFile.url).replace(/\W/g, "");
      Object.defineProperty(HTMLIFrameElement.prototype, "offsetHeight", {
        configurable: true,
        get() {
          if (this.id === iframeId) return 1500;
          return 0;
        },
      });
    });

    it("shows the iFrame at a minimum height", () => {
      const spaDiv = document.createElement("div");
      spaDiv.id = "outputsSPA";
      Object.defineProperty(spaDiv, "offsetHeight", {
        configurable: true,
        value: 1000,
      });
      document.body.appendChild(spaDiv);

      const { container } = render(
        <Iframe
          data={htmlExample}
          fileName={htmlFile.name}
          fileUrl={htmlFile.url}
        />,
      );
      const iframe = container.querySelector("iframe");
      expect(iframe.getAttribute("height")).toBe("1000");

      document.body.removeChild(spaDiv);
    });

    it("shows the iFrame at the height of the SPA container if it is large enough", () => {
      const spaDiv = document.createElement("div");
      spaDiv.id = "outputsSPA";
      Object.defineProperty(spaDiv, "offsetHeight", {
        configurable: true,
        value: 1500,
      });
      document.body.appendChild(spaDiv);

      const { container } = render(
        <Iframe
          data={htmlExample}
          fileName={htmlFile.name}
          fileUrl={htmlFile.url}
        />,
      );
      const iframe = container.querySelector("iframe");
      expect(iframe.getAttribute("height")).toBe("1500");

      document.body.removeChild(spaDiv);
    });
  });
});
