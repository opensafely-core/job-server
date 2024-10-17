import React from "react";
import { describe, expect, it } from "vitest";
import Table from "../../../components/Table/Table";
import { csvExample, csvFile } from "../../helpers/files";
import { render, screen } from "../../test-utils";

describe("<Table />", () => {
  // biome-ignore lint/style/useConsistentBuiltinInstantiation: ESLint to Biome legacy ignore
  const twoThousandRows = `${Array(2000).fill(`b
  `)}`.trimEnd();

  it("displays the CSV mapped to a table", async () => {
    render(<Table data={csvExample} />, {}, { file: csvFile });

    const cells = screen.getAllByRole("cell");
    expect(cells[0].textContent).toEqual("gradually");
    expect(cells[cells.length - 1].textContent).toEqual("select");
  });

  it("displays the first 1000 rows for CSVs with more than 1000 and fewer than 5000 rows", async () => {
    render(<Table data={twoThousandRows} />, {}, { file: csvFile });

    expect(screen.getByRole("alert").textContent).toBe(
      "This is a preview of the first 1000 rows",
    );
    expect(screen.getAllByRole("row").length).toBe(1000);
  });
});
