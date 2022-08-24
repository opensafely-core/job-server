import React, { useEffect } from "react";
import {
  Button,
  Card,
  Col,
  Form,
  ListGroup,
  Modal,
  Row,
} from "react-bootstrap";
import useAppStore from "../../stores/use-app-store";
import useFileStore from "../../stores/use-file-store";

function ReviewModal() {
  const checkedFiles = useFileStore((state) => state.checkedFiles);
  const isModalOpen = useAppStore((state) => state.isModalOpen);
  const hideModal = useAppStore((state) => state.hideModal);
  const { formData, getFormDataMeta, setFormDataFiles, setFormDataMeta } =
    useFileStore((state) => ({
      formData: state.formData,
      getFormDataMeta: state.getFormDataMeta,
      setFormDataFiles: state.setFormDataFiles,
      setFormDataMeta: state.setFormDataMeta,
    }));

  useEffect(() => {
    setFormDataFiles(checkedFiles);
  }, [checkedFiles, isModalOpen, setFormDataFiles]);

  return (
    <Modal
      backdrop="static"
      centered
      keyboard={false}
      show={isModalOpen}
      size="xl"
    >
      <Modal.Header>
        <Modal.Title>Submit review request</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Row className="pb-3">
          <Col>
            <h2 className="h4 mpb-3">Files requested</h2>
            {checkedFiles.map((file) => (
              <Card key={file.id} className="mb-3">
                <Card.Header className="font-weight-bold">
                  {file.shortName}
                </Card.Header>
                {(file.meta["fileForm.context"] ||
                  file.meta["fileForm.disclosureControl"]) && (
                  <ListGroup variant="flush">
                    {file.meta["fileForm.context"] && (
                      <ListGroup.Item>
                        <p className="mb-0">
                          <strong>Describe what this file contains:</strong>
                        </p>
                        <p className="mb-0">{file.meta["fileForm.context"]}</p>
                      </ListGroup.Item>
                    )}
                    {file.meta["fileForm.disclosureControl"] && (
                      <ListGroup.Item>
                        <p className="mb-0">
                          <strong>
                            Describe how you have ensured this file
                            non-disclosive:
                          </strong>
                        </p>
                        <p className="mb-0">
                          {file.meta["fileForm.disclosureControl"]}
                        </p>
                      </ListGroup.Item>
                    )}
                  </ListGroup>
                )}
              </Card>
            ))}
          </Col>
        </Row>
        <Row className="py-3">
          <Col md={{ span: 10, offset: 1 }} xl={{ span: 8, offset: 2 }}>
            <h2 className="h4">Additional information</h2>
            <Form id="modalForm">
              <Form.Group controlId="additionalInformation-1">
                <Form.Label className="mb-0 font-weight-bold">
                  Describe why the data release is necessary to help you meet
                  your project purpose
                </Form.Label>

                <Form.Control
                  as="textarea"
                  className="mt-2"
                  onChange={(e) =>
                    setFormDataMeta("dataRelease", e.target.value)
                  }
                  required
                  rows={4}
                  value={getFormDataMeta("dataRelease")}
                />
                <Form.Text muted>
                  The number of study outputs requested for review must be kept
                  to a minimum and include only the results you absolutely need
                  to export from the server. Because each data release entails
                  substantial review work, and we need to retain rapid
                  turnaround times, external data releases should typically only
                  be of results for final submission to a journal or public
                  notebook; or a small number of necessary releases for
                  discussion with external collaborators.
                </Form.Text>
              </Form.Group>
              <Form.Group className="mt-4">
                <Form.Label
                  className="mb-0 font-weight-bold"
                  htmlFor="readAndAdhere"
                >
                  Confirm that you have read the{" "}
                  <a
                    href="https://docs.opensafely.org/releasing-files"
                    rel="noopener noreferrer"
                    target="_blank"
                  >
                    OpenSAFELY documentation on data release
                  </a>{" "}
                  and that your results adhere to the{" "}
                  <a
                    href="https://www.opensafely.org/policies-for-researchers/#permitted-study-results-policy"
                    rel="noopener noreferrer"
                    target="_blank"
                  >
                    Permitted Study Results Policy
                  </a>
                  .
                </Form.Label>
                <Form.Switch
                  className="mt-2"
                  id="readAndAdhere"
                  label="I confirm the above statement"
                  onChange={(e) =>
                    setFormDataMeta("readAndAdhere", e.target.checked)
                  }
                  type="switch"
                />
              </Form.Group>
              <Form.Group className="mt-4">
                <Form.Label
                  className="mb-0 font-weight-bold"
                  htmlFor="disclosureControls"
                >
                  Have you applied all necessary and relevant disclosure
                  controls to the data for release,{" "}
                  <a
                    href="https://docs.opensafely.org/releasing-files/#1-applying-disclosure-controls-to-data-you-request-for-release"
                    rel="noopener noreferrer"
                    target="_blank"
                  >
                    as detailed in the documentation
                  </a>
                  ?
                </Form.Label>
                <Form.Switch
                  className="mt-2"
                  id="disclosureControls"
                  label="I have applied all necessary and relevant disclosure controls"
                  onChange={(e) =>
                    setFormDataMeta("disclosureControls", e.target.checked)
                  }
                  type="switch"
                />
              </Form.Group>
              <Form.Group className="mt-4">
                <Form.Label
                  className="mb-0 font-weight-bold"
                  htmlFor="fileTypes"
                >
                  Only the following file types will be reviewed: HTML; TXT;
                  CSV; SVG; JPG.
                </Form.Label>
                <Form.Text muted>
                  Please email datarelease@opensafely.org if you need additional
                  file types
                </Form.Text>
                <Form.Switch
                  className="mt-2"
                  id="fileTypes"
                  label="My request only contains the above file types"
                  onChange={(e) =>
                    setFormDataMeta("fileTypes", e.target.checked)
                  }
                  type="switch"
                />
              </Form.Group>
            </Form>
            <pre className="mt-5">{JSON.stringify(formData, null, 2)}</pre>
          </Col>
        </Row>
      </Modal.Body>
      <Modal.Footer>
        <Button
          form="modalForm"
          onClick={() => checkForm()}
          type="submit"
          variant="success"
        >
          Submit request
        </Button>
        <Button onClick={hideModal} variant="secondary">
          Edit request
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default ReviewModal;
