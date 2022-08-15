import { useMutation } from "@tanstack/react-query";
import PropTypes from "prop-types";
import React from "react";
import { toastDismiss, toastError } from "../../utils/toast";
import Button from "./Button";

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

      return response.json();
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
    <Button
      isLoading={mutation.isLoading}
      onClickFn={() => mutation.mutate()}
      text={{ default: "Confirm Publish?", loading: "Confirming…" }}
    />
  );
}

export default PublishButton;

PublishButton.propTypes = {
  csrfToken: PropTypes.string.isRequired,
  publishUrl: PropTypes.string.isRequired,
};
