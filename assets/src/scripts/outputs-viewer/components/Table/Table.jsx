/* eslint-disable react/no-array-index-key */
import PropTypes from "prop-types";
import React from "react";
import { usePapaParse } from "react-papaparse";

function TableCell({ cell }) {
  return <td>{cell}</td>;
}

function TableRow({ row }) {
  return (
    <tr>
      {row.map((cell, i) => (
        <TableCell key={i} cell={cell} />
      ))}
    </tr>
  );
}

function Table({ data }) {
  const { readString } = usePapaParse();

  const jsonData = readString(data, {
    chunk: true,
    complete: (results) => results,
  }).data;

  if (jsonData.length >= 1000) {
    return (
      <>
        <p role="alert">
          <strong>This is a preview of the first 1000 rows</strong>
        </p>
        <div className="table-responsive">
          <table className="table table-striped">
            <tbody>
              {jsonData.slice(0, 1000).map((row, i) => (
                <TableRow key={i} row={row} />
              ))}
            </tbody>
          </table>
        </div>
      </>
    );
  }

  return (
    <div className="table-responsive">
      <table className="table table-striped">
        <tbody>
          {jsonData.map((row, i) => (
            <TableRow key={i} row={row} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Table;

TableCell.propTypes = {
  cell: PropTypes.string.isRequired,
};

TableRow.propTypes = {
  row: PropTypes.arrayOf(PropTypes.string).isRequired,
};

Table.propTypes = {
  data: PropTypes.string.isRequired,
};
