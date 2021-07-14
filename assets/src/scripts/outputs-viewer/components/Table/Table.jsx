import PropTypes from "prop-types";
import React from "react";
import { readString } from "react-papaparse";
import { useTable } from "react-table";

function Table({ data }) {
  let jsonData;

  readString(data, {
    header: true,
    complete: (results) => {
      jsonData = results;
    },
  });

  const memoData = React.useMemo(() => jsonData.data, [data]);

  const columns = React.useMemo(() => {
    const headers = jsonData.meta.fields.map((header) => ({
      accessor: header,
    }));
    return headers;
  }, [data]);

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
