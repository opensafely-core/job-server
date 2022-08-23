import React from "react";
import { Button, Form } from "react-bootstrap";
import useFileStore from "../../stores/use-file-store";

function FileReview({ selectedFile: { id } }) {
  const { addCheckedFile, isFileChecked, removeCheckedFile, checkedFiles } =
    useFileStore((state) => ({
      addCheckedFile: state.addCheckedFile,
      removeCheckedFile: state.removeCheckedFile,
      checkedFiles: state.checkedFiles,
      isFileChecked: state.isFileChecked,
    }));

  const { setFileMeta, getFileMeta } = useFileStore((state) => ({
    setFileMeta: state.setFileMeta,
    getFileMeta: state.getFileMeta,
  }));

  const toggleFileCheck = () => {
    if (isFileChecked(id)) {
      return removeCheckedFile(id);
    }
    return addCheckedFile(id);
  };

  console.log({ checkedFiles });

  return (
    <div className="mb-3">
      <Button
        onClick={() => toggleFileCheck()}
        size="sm"
        variant={isFileChecked(id) ? "danger" : "success"}
      >
        {isFileChecked(id)
          ? "Remove file from review request"
          : "Add file to review request"}
      </Button>
      {isFileChecked(id) ? (
        <Form className="mt-3">
          <Form.Group className="mb-3" controlId={`${id}-fileForm.context`}>
            <Form.Label className="mb-0 font-weight-bold">
              Describe what the file contains
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
                setFileMeta(id, "fileForm.context", e.target.value)
              }
              rows={4}
              value={getFileMeta(id, "fileForm.context")}
            />
          </Form.Group>
          <Form.Group controlId={`${id}-fileForm.disclosureControl`}>
            <Form.Label className="mb-0 font-weight-bold">
              Describe how you have ensured that the files are non-disclosive
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
                setFileMeta(id, "fileForm.disclosureControl", e.target.value)
              }
              rows={4}
              value={getFileMeta(id, "fileForm.disclosureControl")}
            />
          </Form.Group>
        </Form>
      ) : null}
    </div>
  );
}

export default FileReview;
