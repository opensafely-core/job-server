/* eslint-disable react/no-array-index-key */
import PropTypes from "prop-types";
import React from "react";
import { readString } from "react-papaparse";
import useFile from "../../hooks/use-file";
import useStore from "../../stores/use-store";
import NoPreview from "../NoPreview/NoPreview";

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

function Table() {
  const { file } = useStore();
  const { data } = useFile(file);

  const jsonData = readString(data, {
    chunk: true,
    complete: (results) => results,
  }).data;

  if (jsonData.length > 5000) return <NoPreview />;

  if (jsonData.length > 1000) {
    return (
      <>
        <p>
          <strong>This is a preview of the first 1000 lines</strong>
        </p>
        <div className="table-responsive">
          <table className="table table-striped">
            <tbody>
              {jsonData.slice(0, 999).map((row, i) => (
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

TableCell.propTypes = {
  cell: PropTypes.string.isRequired,
};

TableRow.propTypes = {
  row: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default Table;
