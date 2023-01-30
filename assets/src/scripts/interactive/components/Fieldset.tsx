import {
  FormikErrors,
  FormikTouched,
  FormikValues,
  useFormikContext,
} from "formik";
import React from "react";

function Fieldset({
  children,
  legend,
  name,
}: {
  children: React.ReactNode;
  legend: string;
  name: string;
}) {
  const {
    touched,
    errors,
  }: {
    touched: FormikTouched<FormikValues>;
    errors: FormikErrors<FormikValues>;
  } = useFormikContext();

  const isFormFieldValid = () => !!(touched[name] && errors[name]);
  const getFormErrorMessage = () => isFormFieldValid() && errors[name];

  return (
    <fieldset className="mt-12">
      <legend className="text-2xl font-bold mb-4">
        <h2>{legend}</h2>
      </legend>
      <div className="flex flex-col gap-4">
        {children}
        {isFormFieldValid() ? (
          <div>{JSON.stringify(getFormErrorMessage)}</div>
        ) : null}
      </div>
    </fieldset>
  );
}

export default Fieldset;
