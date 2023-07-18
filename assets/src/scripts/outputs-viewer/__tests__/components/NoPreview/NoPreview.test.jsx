import React from "react";
import { describe, expect, it } from "vitest";
import NoPreview from "../../../components/NoPreview/NoPreview";
import { server, rest } from "../../__mocks__/server";
import { pngFile } from "../../helpers/files";
import { render, screen, waitFor } from "../../test-utils";

describe("<NoPreview />", () => {
  it("shows the no preview message", async () => {
    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ data: {} })),
      ),
    );

    render(<NoPreview fileUrl={pngFile.url} />);

    await waitFor(
      () =>
        expect(screen.getByText("We cannot show a preview of this file."))
          .toBeVisible,
    );
  });

  it("shows an error message", async () => {
    const err = { message: "There was an error" };

    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ data: {} })),
      ),
    );

    render(<NoPreview error={err} fileUrl={pngFile.url} />);

    await waitFor(
      () =>
        expect(screen.getByText("We cannot show a preview of this file."))
          .toBeVisible,
    );
    await waitFor(
      () => expect(screen.getByText(`Error: There was an error`)).toBeVisible,
    );
  });
});
