import React from "react";
import NoPreview from "../../../components/NoPreview/NoPreview";
import useStore from "../../../stores/use-store";
import { server, rest } from "../../__mocks__/server";
import { pngFile } from "../../helpers/files";
import { render, screen, waitFor } from "../../test-utils";

describe("<NoPreview />", () => {
  beforeEach(() => {
    useStore.setState((state) => ({
      ...state,
      file: pngFile,
    }));
  });

  it("shows the no preview message", async () => {
    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ data: {} }))
      )
    );

    render(<NoPreview />);

    await waitFor(
      () =>
        expect(screen.getByText("We cannot show a preview of this file."))
          .toBeVisible
    );
  });

  it("shows an error message", async () => {
    const err = "There was an error";

    server.use(
      rest.get(`http://localhost${pngFile.url}`, (req, res, ctx) =>
        res(ctx.status(200), ctx.json({ data: {} }))
      )
    );

    render(<NoPreview error={err} />);

    await waitFor(
      () =>
        expect(screen.getByText("We cannot show a preview of this file."))
          .toBeVisible
    );
    await waitFor(() => expect(screen.getByText(`Error: ${err}`)).toBeVisible);
  });
});
