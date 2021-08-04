/* eslint-disable react/no-array-index-key */
import PropTypes from "prop-types";
import React from "react";
import { readString } from "react-papaparse";
import useStore from "../../stores/use-store";

const TableCell = ({ cell }) => <td>{cell}</td>;

const TableRow = ({ row }) => (
  <tr>
    {row.map((cell, i) => (
      <TableCell key={i} cell={cell} />
    ))}
  </tr>
);

function Table({ data }) {
  const { file } = useStore();

  const jsonData = readString(data, {
    chunk: true,
    complete: (results) => results,
  }).data;

  if (jsonData.length > 1000) {
    return (
      <>
        <p>We cannot show a preview of this file.</p>
        <p className="mb-0">
          <a href={file.url} rel="noreferrer noopener" target="_blank">
            Open file in a new tab &#8599;
          </a>
        </p>
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
