import { useFormikContext } from "formik";
import { useEffect } from "react";
import { useFormData } from "../context";

const beforeUnloadListener = (event) => {
  event.preventDefault();
  // https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event#examples
  // @ts-ignore
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
  const { formData } = useFormData();
  const { dirty } = useFormikContext();

  useEffect(() => {
    if (dirty || !!Object.keys(formData).length) {
      return addAlert();
    }
    return removeAlert();
  }, [dirty, formData]);

  return null;
}

export function AlertPage() {
  const { formData } = useFormData();

  useEffect(() => {
    if (formData) {
      return addAlert();
    }
    return removeAlert();
  }, [formData]);

  return null;
}
