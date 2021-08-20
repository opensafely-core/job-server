import React from "react";
import Metadata from "../../../components/Metadata/Metadata";
import { pngFile } from "../../helpers/files";
import { render, screen } from "../../test-utils";

describe("<Metadata />", () => {
  it("show metadata", () => {
    render(<Metadata file={pngFile} />);

    // File link
    expect(screen.getByRole("link").href).toBe(
      `http://localhost${pngFile.url}`
    );

    // Absolute date
    expect(screen.getByText("01/01/2021, 10:11").getAttribute("datetime")).toBe(
      "2021-01-01T10:11:12.131Z"
    );

    // Date
    expect(screen.getByText("01/01/2021, 10:11")).toBeVisible();

    // File size
    expect(screen.getByText("1.23 kB")).toBeVisible();
  });

  it("shows unknown for file size if file size not provided", () => {
    // eslint-disable-next-line no-console
    console.error = jest.fn();

    render(<Metadata file={{ ...pngFile, size: null }} />);

    // File link
    expect(screen.getByRole("link").href).toBe(
      `http://localhost${pngFile.url}`
    );

    // Absolute date
    expect(screen.getByText("01/01/2021, 10:11").getAttribute("datetime")).toBe(
      "2021-01-01T10:11:12.131Z"
    );

    // Date
    expect(screen.getByText("01/01/2021, 10:11")).toBeVisible();

    // File size
    expect(screen.getByText("unknown")).toBeVisible();
  });
});
