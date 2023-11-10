import { useMutation } from "@tanstack/react-query";
import React from "react";
import useFileList from "../../hooks/use-file-list";
import { datasetProps } from "../../utils/props";
import { toastDismiss, toastError } from "../../utils/toast";
import Button from "./Button";

function PrepareButton({ authToken, csrfToken, filesUrl, prepareUrl }) {
  const { data: fileList } = useFileList({ authToken, filesUrl });
  const toastId = "PrepareButton";

  const mutation = useMutation({
    mutationFn: async (fileIds) => {
      const response = await fetch(prepareUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ file_ids: fileIds }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }

      return response.json();
    },
    // mutationKey: "PREPARE_RELEASE",
    onMutate: () => {
      toastDismiss({ toastId });
    },
    onSuccess: (data) => {
      // redirect to URL returned from the API
      window.location.href = data.url;
    },
    onError: (error) => {
      toastError({
        message: `${error}`,
        toastId,
        prepareUrl,
        url: document.location.href,
      });
    },
  });

  if (!fileList?.length) return null;

  const fileIds = fileList.map((f) => f.id);

  return (
    <Button
      disabled={mutation.isPending}
      onClick={(e) => {
        e.preventDefault();
        return mutation.mutate(fileIds);
      }}
      type="button"
      variant={mutation.isPending ? "secondary" : "primary"}
    >
      {mutation.isPending ? "Creating…" : "Create a draft publication"}
    </Button>
  );
}

export default PrepareButton;

PrepareButton.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  csrfToken: datasetProps.csrfToken.isRequired,
  filesUrl: datasetProps.filesUrl.isRequired,
  prepareUrl: datasetProps.prepareUrl.isRequired,
};
