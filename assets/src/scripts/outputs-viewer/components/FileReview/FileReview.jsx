import PropTypes from "prop-types";
import React from "react";
import { Button, Form } from "react-bootstrap";
import useFileStore from "../../stores/use-file-store";
import { selectedFileProps } from "../../utils/props";

function FileReview({ selectedFile }) {
  const { addCheckedFile, isFileChecked, removeCheckedFile } = useFileStore(
    (state) => ({
      addCheckedFile: state.addCheckedFile,
      removeCheckedFile: state.removeCheckedFile,
      checkedFiles: state.checkedFiles,
      isFileChecked: state.isFileChecked,
    })
  );

  const { setFileMeta, getFileMeta } = useFileStore((state) => ({
    setFileMeta: state.setFileMeta,
    getFileMeta: state.getFileMeta,
  }));

  const toggleFileCheck = () => {
    if (isFileChecked(selectedFile)) {
      return removeCheckedFile(selectedFile);
    }
    return addCheckedFile(selectedFile);
  };

  return (
    <div className="mb-3">
      <Button
        onClick={() => toggleFileCheck()}
        size="sm"
        variant={isFileChecked(selectedFile) ? "danger" : "success"}
      >
        {isFileChecked(selectedFile)
          ? "Remove file from review request"
          : "Add file to review request"}
      </Button>
      {isFileChecked(selectedFile) ? (
        <Form className="mt-3">
          <Form.Group
            className="mb-3"
            controlId={`${selectedFile.id}-fileForm.context`}
          >
            <Form.Label className="mb-0 font-weight-bold">
              Describe what this file contains
            </Form.Label>
            <Form.Text muted>
              <strong>For example:</strong> Monthly hospitalisation counts of
              people with cancer (and covid infection status), cut by ethnicity,
              in all registered patients in England from March 2020 to July
              2020. This is the underlying data for output
              #2-cancer_hospitalisation_ethnicity.svg.
            </Form.Text>
            <Form.Control
              as="textarea"
              className="mt-2"
              onChange={(e) =>
                setFileMeta(selectedFile, "context", e.target.value)
              }
              rows={4}
              value={getFileMeta(selectedFile, "context")}
            />
          </Form.Group>
          <Form.Group
            controlId={`${selectedFile.id}-fileForm.disclosureControl`}
          >
            <Form.Label className="mb-0 font-weight-bold">
              Describe how you have ensured that this file is non-disclosive
            </Form.Label>
            <Form.Text muted>
              <strong>For example:</strong> Low number suppression has been
              applied to remove any monthly counts &lt;=5 within all cells.
              Rounding to the nearest 5/7/10 has also been applied to all
              outputs to further protect against small number differences.
            </Form.Text>
            <Form.Control
              as="textarea"
              className="mt-2"
              onChange={(e) =>
                setFileMeta(selectedFile, "disclosureControl", e.target.value)
              }
              rows={4}
              value={getFileMeta(selectedFile, "disclosureControl")}
            />
          </Form.Group>
        </Form>
      ) : null}
    </div>
  );
}

export default FileReview;

FileReview.propTypes = {
  selectedFile: PropTypes.shape(selectedFileProps).isRequired,
};
