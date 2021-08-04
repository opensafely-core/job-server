/* eslint-disable react/no-array-index-key */
import PropTypes from "prop-types";
import React from "react";
import { readString } from "react-papaparse";

const TableCell = ({ cell }) => <td>{cell}</td>;

const TableRow = ({ row }) => (
  <tr>
    {row.map((cell, i) => (
      <TableCell key={i} cell={cell} />
    ))}
  </tr>
);

function Table({ data }) {
  const jsonData = readString(data, {
    chunk: true,
    complete: (results) => results,
  }).data;

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

TableCell.propTypes = {
  cell: PropTypes.string.isRequired,
};

TableRow.propTypes = {
  row: PropTypes.arrayOf(PropTypes.string).isRequired,
};

Table.propTypes = {
  data: PropTypes.string.isRequired,
};

export default Table;
