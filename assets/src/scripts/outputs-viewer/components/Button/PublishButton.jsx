import React from "react";
import { useMutation } from "react-query";
import useStore from "../../stores/use-store";
import handleErrors from "../../utils/fetch-handle-errors";
import Button from "./Button";

function PublishButton() {
  const { csrfToken, publishUrl } = useStore();

  const mutation = useMutation(
    () =>
      fetch(publishUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
      }).then(handleErrors),
    {
      mutationKey: "PUBLISH_RELEASE",
      onSuccess: () => {
        // redirect to URL returned from the API
        window.location.reload();
      },
      onError: (error) => {
        // eslint-disable-next-line no-console
        console.error("Error", { error });
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
