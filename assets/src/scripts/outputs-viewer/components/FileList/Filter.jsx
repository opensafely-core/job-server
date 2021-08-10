import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import useFileList from "../../hooks/use-file-list";

function Filter({ className, listRef, setFiles }) {
  const { data } = useFileList();
  const [filter, setFilter] = useState("");

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

  function filterOnChange(e) {
    listRef?.current?.scrollToItem(0);
    setFilter(e.target.value);
  }

  return (
    <label className={`w-100 ${className}`} htmlFor="filterFiles">
      <span className="sr-only">Find a file…</span>
      <input
        autoCapitalize="off"
        autoComplete="off"
        autoCorrect="off"
        className="form-control mb-0"
        id="filterFiles"
        onChange={(e) => filterOnChange(e)}
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
  className: PropTypes.string,
  listRef: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.shape({ current: PropTypes.instanceOf(Element) }),
  ]).isRequired,
  setFiles: PropTypes.func.isRequired,
};

Filter.defaultProps = {
  className: "",
};
