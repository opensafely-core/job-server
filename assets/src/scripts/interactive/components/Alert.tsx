import { useFormikContext } from "formik";
import { useEffect } from "react";
import { useFormStore } from "../stores";

const beforeUnloadListener = (event: Event) => {
  event.preventDefault();
  // https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event#examples
  // @ts-ignore
  // eslint-disable-next-line no-return-assign, no-param-reassign
  return (event.returnValue = "");
};

function addAlert() {
  return window.addEventListener("beforeunload", beforeUnloadListener, {
    capture: true,
  });
}

export function removeAlert() {
  return window.removeEventListener("beforeunload", beforeUnloadListener, {
    capture: true,
  });
}

export function AlertForm() {
  const { formData } = useFormStore.getState();
  const { dirty } = useFormikContext();

  useEffect(() => {
    if (dirty || !!Object.keys(formData).length) {
      return addAlert();
    }
    return removeAlert();
  }, [dirty, formData]);

  return null;
}

AlertForm.defaultProps = {
  hasForm: false,
};

export function AlertPage() {
  const { formData } = useFormStore.getState();

  useEffect(() => {
    if (formData) {
      return addAlert();
    }
    return removeAlert();
  }, [formData]);

  return null;
}
