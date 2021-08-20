import axios from "axios";
import React from "react";
import { useMutation } from "react-query";
import useFileList from "../../hooks/use-file-list";
import useStore from "../../stores/use-store";
import { toastDismiss, toastError } from "../../utils/toast";
import Button from "./Button";

function PrepareButton() {
  const { csrfToken, prepareUrl } = useStore();
  const { data: fileList } = useFileList();
  const toastId = "PrepareButton";

  const mutation = useMutation(
    ({ fileIds }) =>
      axios
        .post(
          prepareUrl,
          { file_ids: fileIds },
          {
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
            },
          }
        )
        .then((response) => response.data)
        .catch((error) => {
          throw error?.response?.data?.detail || error;
        }),
    {
      mutationKey: "PREPARE_RELEASE",
      onMutate: () => {
        toastDismiss({ toastId });
      },
      onSuccess: (data) => {
        // redirect to URL returned from the API
        window.location.href = data.url;
      },
      onError: (err) => {
        toastError({
          message: `${err}`,
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
