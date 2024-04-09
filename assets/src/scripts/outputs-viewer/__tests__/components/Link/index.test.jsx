import React from "react";
import { describe, expect, it } from "vitest";
import Link from "../../../components/Link";
import { render, screen } from "../../test-utils";

describe("<Link />", () => {
  it("Displays the content of the link", async () => {
    render(<Link href="/hello-world/">Hello world</Link>);

    const link = await screen.findByRole("link", { name: "Hello world" });
    expect(link).toBeVisible();
    expect(link.getAttribute("href")).toBe("/hello-world/");
  });

  it("Opens a link in a new target tab", async () => {
    render(
      <Link href="/hello-world/" newTab>
        Hello world
      </Link>,
    );

    const link = await screen.findByRole("link", { name: "Hello world" });
    expect(link).toBeVisible();
    expect(link.getAttribute("rel")).toBe("noreferrer noopener");
    expect(link.getAttribute("target")).toBe("filePreview");
  });
});
