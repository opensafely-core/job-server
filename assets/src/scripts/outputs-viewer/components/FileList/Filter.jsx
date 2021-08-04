import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import useFileList from "../../hooks/use-file-list";

function Filter({ setFiles }) {
  const { data } = useFileList();
  const [filter, setFilter] = useState("");

  useEffect(() => {
    if (data) {
      return filter
        ? setFiles(data.filter((item) => item.shortName.includes(filter)))
        : setFiles(data);
    }

    return setFiles([]);
  }, [data, filter, setFiles]);

  return (
    <label className="w-100" htmlFor="filterFiles">
      <span className="sr-only">Filter files</span>
      <input
        className="form-control"
        id="filterFiles"
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter files"
        type="search"
        value={filter}
      />
    </label>
  );
}

export default Filter;

Filter.propTypes = {
  setFiles: PropTypes.func.isRequired,
};
