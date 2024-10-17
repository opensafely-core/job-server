import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import FormInput from "../Form/Input";

function Filter({ files, listRef, setFiles }) {
  const [filter, setFilter] = useState("");

  // biome-ignore lint/correctness/useExhaustiveDependencies: ESLint to Biome legacy ignore
  useEffect(() => {
    const filteredFiles = [...files].map((file) => ({
      ...file,
      visible: file.shortName.toLowerCase().includes(filter.toLowerCase()),
    }));

    setFiles(filteredFiles);
  }, [filter]);

  function filterOnChange(e) {
    listRef?.current?.scrollToItem(0);
    setFilter(e.target.value);
  }

  return (
    <FormInput
      autocapitalize="off"
      autocomplete="off"
      autocorrect="off"
      className="mb-1"
      hideLabel
      id="filterFiles"
      label="Find a file…"
      onChange={(e) => filterOnChange(e)}
      placeholder="Find a file…"
      type="search"
      value={filter}
    />
  );
}

export default Filter;

Filter.propTypes = {
  files: PropTypes.arrayOf(PropTypes.shape()).isRequired,
  listRef: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.shape({ current: PropTypes.instanceOf(Element) }),
  ]).isRequired,
  setFiles: PropTypes.func.isRequired,
};
