import PropTypes from "prop-types";
import React from "react";
import { useMutation } from "react-query";
import useFileList from "../../hooks/use-file-list";
import handleErrors from "../../utils/fetch-handle-errors";
import Button from "./Button";

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
      mutationKey: "PREPARE_RELEASE",
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

  if (!fileList) return null;

  const fileIds = fileList.map((f) => f.id);

  return (
    <Button
      isLoading={mutation.isLoading}
      onClickFn={() => mutation.mutate({ fileIds })}
      text={{ default: "Publish", loading: "Publishing…" }}
    />
  );
}

PrepareButton.propTypes = {
  csrfToken: PropTypes.string.isRequired,
  filesUrl: PropTypes.string.isRequired,
  prepareUrl: PropTypes.string.isRequired,
};

export default PrepareButton;
