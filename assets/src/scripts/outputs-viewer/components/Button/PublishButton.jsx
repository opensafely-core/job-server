import { useMutation } from "@tanstack/react-query";
import React from "react";
import { datasetProps } from "../../utils/props";
import { toastDismiss, toastError } from "../../utils/toast";

function PublishButton({ csrfToken, publishUrl }) {
  const toastId = "PublishButton";

  const mutation = useMutation(
    async () => {
      const response = await fetch(publishUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }

      return response.text();
    },
    {
      mutationKey: "PUBLISH_RELEASE",
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
    }
  );

  return (
    <button
      className={`btn btn-${mutation.isLoading ? "secondary" : "primary"}`}
      disabled={mutation.isLoading}
      onClick={(e) => {
        e.preventDefault();
        return mutation.mutate();
      }}
      type="button"
    >
      {mutation.isLoading ? "Confirming…" : "Confirm Publish?"}
    </button>
  );
}

export default PublishButton;

PublishButton.propTypes = {
  csrfToken: datasetProps.csrfToken.isRequired,
  publishUrl: datasetProps.publishUrl.isRequired,
};
