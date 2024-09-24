import { toast } from "react-toastify";

export function toastDismiss({ toastId }) {
  toast.dismiss(toastId);
}

export function toastError({ toastId, message, ...args }) {
  // eslint-disable-next-line no-console
  console.error(message, { ...args });

  toast.error(message, {
    autoClose: false,
    closeOnClick: false,
    draggable: false,
    hideProgressBar: true,
    id: toastId,
    pauseOnHover: false,
    position: "top-right",
    theme: "light",
  });
}
