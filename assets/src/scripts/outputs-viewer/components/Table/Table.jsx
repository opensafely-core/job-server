import PropTypes from "prop-types";
import React from "react";
import { readString } from "react-papaparse";
import { useTable } from "react-table";

function Table({ data }) {
  const memoData = React.useMemo(
    () =>
      readString(data, {
        header: true,
        complete: (results) => results,
      }).data,
    [data]
  );

  const columns = React.useMemo(
    () =>
      readString(data, {
        header: true,
        complete: (results) => results,
      }).meta.fields.map((header) => ({
        accessor: header,
      })),
    [data]
  );

  const { getTableProps, getTableBodyProps, rows, prepareRow } = useTable({
    columns,
    data: memoData,
  });

  return (
    <table {...getTableProps()}>
      <tbody {...getTableBodyProps()}>
        {rows.map((row) => {
          prepareRow(row);
          return (
            <tr {...row.getRowProps()}>
              {row.cells.map((cell) => (
                <td {...cell.getCellProps()}>{cell.render("Cell")}</td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

Table.propTypes = {
  data: PropTypes.string.isRequired,
};

export default Table;
