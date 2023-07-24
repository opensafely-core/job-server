import React from "react";
import { describe, expect, it, test, vi } from "vitest";
import Metadata from "../../../components/Metadata/Metadata";
import { pngFile } from "../../helpers/files";
import { render, screen } from "../../test-utils";

describe("<Metadata />", () => {
  test("if date is invalid, return nothing", () => {
    render(
      <Metadata
        fileDate="asdadsdasd"
        fileName={pngFile.name}
        fileSize={pngFile.size}
        fileUrl={pngFile.url}
      />,
    );

    expect(screen.queryByText("01/01/2021, 10:11")).not.toBeInTheDocument();
  });

  it("show metadata", () => {
    render(
      <Metadata
        fileDate={pngFile.date}
        fileName={pngFile.name}
        fileSize={pngFile.size}
        fileUrl={pngFile.url}
      />,
    );

    // File link
    expect(screen.getByRole("link").href).toBe(
      `http://localhost:3000${pngFile.url}`,
    );

    // Absolute date
    expect(screen.getByText("01/01/2021, 10:11").getAttribute("datetime")).toBe(
      "2021-01-01T10:11:12.131Z",
    );

    // Date
    expect(screen.getByText("01/01/2021, 10:11")).toBeVisible();

    // File size
    expect(screen.getByText("1.23 kB")).toBeVisible();
  });

  it("shows unknown for file size if file size not provided", () => {
    // eslint-disable-next-line no-console
    console.error = vi.fn();

    render(
      <Metadata
        fileDate={pngFile.date}
        fileName={pngFile.name}
        fileSize={0}
        fileUrl={pngFile.url}
      />,
    );

    // File link
    expect(screen.getByRole("link").href).toBe(
      `http://localhost:3000${pngFile.url}`,
    );

    // Absolute date
    expect(screen.getByText("01/01/2021, 10:11").getAttribute("datetime")).toBe(
      "2021-01-01T10:11:12.131Z",
    );

    // Date
    expect(screen.getByText("01/01/2021, 10:11")).toBeVisible();

    // File size
    expect(screen.getByText("unknown")).toBeVisible();
  });
});
