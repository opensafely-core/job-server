import { useMutation } from "@tanstack/react-query";
import React from "react";
import { datasetProps } from "../../utils/props";
import { toastDismiss, toastError } from "../../utils/toast";
import Button from "./Button";

function PublishButton({ csrfToken, publishUrl }) {
  const toastId = "PublishButton";

  const mutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(publishUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: "",
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }

      return response.text();
    },
    onMutate: () => {
      toastDismiss({ toastId });
    },
    onSuccess: () => {
      // redirect to URL returned from the API
      window.location.reload();
    },
    onError: (error) => {
      toastError({
        message: `${error}`,
        toastId,
        publishUrl,
        url: document.location.href,
      });
    },
  });

  return (
    <Button
      disabled={mutation.isPending}
      onClick={(e) => {
        e.preventDefault();
        return mutation.mutate();
      }}
      type="button"
      variant={mutation.isPending ? "secondary" : "primary"}
    >
      {mutation.isPending ? "Creating…" : "Create a public published output"}
    </Button>
  );
}

export default PublishButton;

PublishButton.propTypes = {
  csrfToken: datasetProps.csrfToken.isRequired,
  publishUrl: datasetProps.publishUrl.isRequired,
};
