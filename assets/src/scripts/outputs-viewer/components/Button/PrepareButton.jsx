import { useMutation } from "@tanstack/react-query";
import React from "react";
import { Button } from "react-bootstrap";
import useFileList from "../../hooks/use-file-list";
import useAppStore from "../../stores/use-app-store";
import { toastDismiss, toastError } from "../../utils/toast";

function PrepareButton() {
  const { data: fileList } = useFileList({ setSelectedFile: null });
  const [csrfToken, prepareUrl] = useAppStore((state) => [
    state.csrfToken,
    state.prepareUrl,
  ]);
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
      disabled={mutation.isLoading}
      onClick={(e) => {
        e.preventDefault();
        return mutation.mutate({ fileIds });
      }}
      type="button"
      variant={mutation.isLoading ? "secondary" : "primary"}
    >
      {mutation.isLoading ? "Publishing…" : "Publish"}
    </Button>
  );
}

export default PrepareButton;
