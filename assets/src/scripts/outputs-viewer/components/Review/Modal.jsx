import { useMutation } from "@tanstack/react-query";
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
import { toastError } from "../../utils/toast";

function ReviewModal() {
  const checkedFiles = useFileStore((state) => state.checkedFiles);
  const [hideModal, isModalOpen] = useAppStore((state) => [
    state.hideModal,
    state.isModalOpen,
  ]);
  const [authToken, reviewUrl] = useAppStore((state) => [
    state.authToken,
    state.reviewUrl,
  ]);
  const { formData, getFormDataMeta, setFormDataFiles, setFormDataMeta } =
    useFileStore((state) => ({
      formData: state.formData,
      getFormDataMeta: state.getFormDataMeta,
      setFormDataFiles: state.setFormDataFiles,
      setFormDataMeta: state.setFormDataMeta,
    }));

  const mutation = useMutation(
    async () => {
      const response = await fetch(reviewUrl, {
        method: "POST",
        headers: {
          Authorization: authToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ...formData }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }

      return response.json();
    },
    {
      mutationKey: "PREPARE_RELEASE",
      onSuccess: (data) => {
        // redirect to URL returned from the API
        window.location.href = data.release_url;
      },
      onError: (error) => {
        toastError({
          message: `${error}`,
          toastId: "reviewModal",
          reviewUrl,
          url: document.location.href,
        });
      },
    }
  );

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
              <Card key={file.sha256} className="mb-3">
                <Card.Header className="font-weight-bold">
                  {file.name}
                </Card.Header>
                {(file.metadata?.context ||
                  file.metadata?.disclosureControl) && (
                  <ListGroup variant="flush">
                    {file.metadata?.context && (
                      <ListGroup.Item>
                        <p className="mb-0">
                          <strong>Describe what this file contains:</strong>
                        </p>
                        <p className="mb-0">{file.metadata?.context}</p>
                      </ListGroup.Item>
                    )}
                    {file.metadata?.disclosureControl && (
                      <ListGroup.Item>
                        <p className="mb-0">
                          <strong>
                            Describe how you have ensured this file
                            non-disclosive:
                          </strong>
                        </p>
                        <p className="mb-0">
                          {file.metadata?.disclosureControl}
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
            <Form
              id="modalForm"
              onSubmit={(e) => {
                e.preventDefault();
                mutation.mutate();
              }}
            >
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
            </Form>
          </Col>
        </Row>
      </Modal.Body>
      <Modal.Footer>
        <Button
          form="modalForm"
          onClick={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
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
