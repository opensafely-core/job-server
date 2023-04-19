import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import { Form } from "react-bootstrap";

function Filter({ files, listRef, setFiles }) {
  const [filter, setFilter] = useState("");

  useEffect(() => {
    if (filter) {
      const timer = setTimeout(
        () =>
          setFiles(
            files.filter((state) =>
              state.name.toLowerCase().includes(filter.toLowerCase())
            )
          ),
        350
      );

      return () => clearTimeout(timer);
    }

    return setFiles(files);
  }, [files, filter, setFiles]);

  function filterOnChange(e) {
    listRef?.current?.scrollToItem(0);
    setFilter(e.target.value);
  }

  return (
    <Form.Group className="mb-1" controlId="filterFiles">
      <Form.Label className="sr-only">Find a file…</Form.Label>
      <Form.Control
        autoCapitalize="off"
        autoComplete="off"
        autoCorrect="off"
        onChange={(e) => filterOnChange(e)}
        placeholder="Find a file…"
        spellCheck="false"
        type="search"
        value={filter}
      />
    </Form.Group>
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
