import axios from "axios";
import React from "react";
import { useMutation } from "react-query";
import useStore from "../../stores/use-store";
import { toastDismiss, toastError } from "../../utils/toast";
import Button from "./Button";

function PublishButton() {
  const { csrfToken, publishUrl } = useStore();
  const toastId = "PublishButton";

  const mutation = useMutation(
    () =>
      axios
        .post(publishUrl, null, {
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
        })
        .then((response) => response.data)
        .catch((error) => {
          throw error?.response?.data?.detail || error;
        }),
    {
      mutationKey: "PUBLISH_RELEASE",
      onMutate: () => {
        toastDismiss({ toastId });
      },
      onSuccess: () => {
        // redirect to URL returned from the API
        window.location.reload();
      },
      onError: (err) => {
        toastError({
          message: `${err}`,
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
