import PropTypes from "prop-types";
import React from "react";
import { useMutation } from "react-query";
import handleErrors from "../../utils/fetch-handle-errors";
import Button from "./Button";

function PublishButton({ csrfToken, publishUrl }) {
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

PublishButton.propTypes = {
  csrfToken: PropTypes.string.isRequired,
  publishUrl: PropTypes.string.isRequired,
};

export default PublishButton;
