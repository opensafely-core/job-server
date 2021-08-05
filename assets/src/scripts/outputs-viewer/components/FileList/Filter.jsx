import PropTypes from "prop-types";
import React, { useEffect, useRef, useState } from "react";
import useFileList from "../../hooks/use-file-list";

function Filter({ setFiles }) {
  const { data } = useFileList();
  const [filter, setFilter] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (filter) {
      const timer = setTimeout(
        () =>
          setFiles(
            data.filter((state) =>
              state.shortName.toLowerCase().includes(filter.toLowerCase())
            )
          ),
        350
      );

      return () => clearTimeout(timer);
    }

    if (data) return setFiles(data);

    return setFiles([]);
  }, [data, filter, setFiles]);

  return (
    <label className="w-100" htmlFor="filterFiles">
      <span className="sr-only">Find a file…</span>
      <input
        ref={inputRef}
        autoCapitalize="off"
        autoComplete="off"
        autoCorrect="off"
        className="form-control mb-0"
        id="filterFiles"
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Find a file…"
        spellCheck="false"
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
