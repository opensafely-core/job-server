/* eslint-disable react/no-array-index-key */
import PropTypes from "prop-types";
import React from "react";
import { usePapaParse } from "react-papaparse";

function TableCell({ cell }) {
  return <td className="py-2 px-2 text-sm text-gray-900">{cell}</td>;
}

function TableRow({ row }) {
  return (
    <tr className="divide-x divide-gray-200 even:bg-gray-50">
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
        <div className="flow-root">
          <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
            <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
              <table className="min-w-full divide-y divide-gray-300">
                <tbody className="divide-y divide-gray-200 bg-white">
                  {jsonData.slice(0, 1000).map((row, i) => (
                    <TableRow key={i} row={row} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="flow-root">
      <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
          <table className="min-w-full divide-y divide-gray-300">
            <tbody className="divide-y divide-gray-200 bg-white">
              {jsonData.map((row, i) => (
                <TableRow key={i} row={row} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
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
