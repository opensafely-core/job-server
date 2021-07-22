import PropTypes from "prop-types";
import React from "react";
import { useMutation } from "react-query";
import useFileList from "../../hooks/use-file-list";
import handleErrors from "../../utils/fetch-handle-errors";

function PrepareButton({ csrfToken, filesUrl, prepareUrl }) {
  const { data: fileList } = useFileList({ apiUrl: filesUrl });

  const mutation = useMutation(
    ({ fileIds }) =>
      fetch(prepareUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ file_ids: fileIds }),
      })
        .then(handleErrors)
        .then((response) => response.json()),
    {
      mutationKey: "PUBLISH_RELEASE",
      onSuccess: (data) => {
        // redirect to URL returned from the API
        window.location.href = data.url;
      },
      onError: (error) => {
        // eslint-disable-next-line no-console
        console.error("Error", { error });
      },
    }
  );

  const onPublish = ({ e, fileIds }) => {
    e.preventDefault();
    mutation.mutate({ fileIds });
  };

  if (!fileList) return null;

  const fileIds = fileList.files.map((f) => f.id);

  return (
    <button
      className={`btn btn-${mutation.isLoading ? "secondary" : "primary"}`}
      disabled={mutation.isLoading}
      onClick={(e) => onPublish({ e, fileIds })}
      type="button"
    >
      {mutation.isLoading ? "Publishing…" : "Publish"}
    </button>
  );
}

PrepareButton.propTypes = {
  csrfToken: PropTypes.string.isRequired,
  filesUrl: PropTypes.string.isRequired,
  prepareUrl: PropTypes.string.isRequired,
};

export default PrepareButton;
