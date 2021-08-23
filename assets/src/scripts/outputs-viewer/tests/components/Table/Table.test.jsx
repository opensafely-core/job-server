import React from "react";
import Table from "../../../components/Table/Table";
import useStore from "../../../stores/use-store";
import { csvExample, csvFile } from "../../helpers/files";
import { render, screen } from "../../test-utils";

describe("<Table />", () => {
  const fiveThousandRows = `${Array(5000).fill(`a
  `)}`.trimEnd();

  const twoThousandRows = `${Array(2000).fill(`b
  `)}`.trimEnd();

  beforeEach(() => {
    useStore.setState((state) => ({
      ...state,
      file: csvFile,
    }));
  });

  it("displays the CSV mapped to a table", async () => {
    render(<Table data={csvExample} />);

    const cells = screen.getAllByRole("cell");
    expect(cells[0].textContent).toEqual("gradually");
    expect(cells[cells.length - 1].textContent).toEqual("select");
  });

  it("displays the <NoPreview /> component for CSVs with more than 5000 rows", async () => {
    render(<Table data={fiveThousandRows} />);

    expect(screen.getByRole("link").textContent).toBe(
      "Open file in a new tab ↗"
    );
    expect(screen.getByRole("link").href).toEqual(
      `http://localhost${csvFile.url}`
    );
  });

  it("displays the first 1000 rows for CSVs with more than 1000 and fewer than 5000 rows", async () => {
    render(<Table data={twoThousandRows} />);

    expect(screen.getByRole("alert").textContent).toBe(
      "This is a preview of the first 1000 rows"
    );
    expect(screen.getAllByRole("row").length).toBe(1000);
  });
});
