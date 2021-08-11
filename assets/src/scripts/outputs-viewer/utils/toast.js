/* eslint-disable no-console */
import toast from "react-hot-toast";

export function toastDismiss({ toastId }) {
  toast.dismiss(toastId);
}

export function toastError({ toastId, message, ...args }) {
  console.error(message, { ...args });

  toast.error(message, {
    id: toastId,
  });
}
