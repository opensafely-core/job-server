import React from "react";
import { useMutation } from "react-query";
import { useFiles } from "../../context/FilesProvider";
import useFileList from "../../hooks/use-file-list";
import { toastDismiss, toastError } from "../../utils/toast";
import Button from "./Button";

function PrepareButton() {
  const {
    state: { csrfToken, prepareUrl },
  } = useFiles();
  const { data: fileList } = useFileList();
  const toastId = "PrepareButton";

  const mutation = useMutation(
    async ({ fileIds }) => {
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
    {
      mutationKey: "PREPARE_RELEASE",
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
    }
  );

  if (!fileList?.length) return null;

  const fileIds = fileList.map((f) => f.id);

  return (
    <Button
      isLoading={mutation.isLoading}
      onClickFn={() => mutation.mutate({ fileIds })}
      text={{ default: "Publish", loading: "Publishing…" }}
    />
  );
}

export default PrepareButton;
