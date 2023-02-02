import { Field, FormikValues, useFormikContext } from "formik";
import {
  builderTimeEvents,
  builderTimeScales,
  endDate,
} from "../data/form-fields";
import { useFormStore } from "../stores";
import { FormDataTypes, SingleCodelist } from "../types";
import { classNames } from "../utils";
import InputError from "./InputError";
import SelectBox from "./SelectBox";

export const lines = [
  "added to their health record in the period between",
  "1st September 2019",
  "and",
  "who have also had",
  "added to their health record from",
];

function CodelistBuilder() {
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const { values, setFieldValue, errors, touched } =
    useFormikContext<FormikValues>();

  const handleChange = (selectedItem: SingleCodelist) => {
    if (selectedItem === values.codelistA) {
      setFieldValue("codelistA", values.codelistB);
      setFieldValue("codelistB", selectedItem);
    }
    if (selectedItem === values.codelistB) {
      setFieldValue("codelistB", values.codelistA);
      setFieldValue("codelistA", selectedItem);
    }
  };

  return (
    <div className="flex flex-col gap-y-3">
      <p className="max-w-prose text-lg">The number of people who had</p>
      <SelectBox
        defaultValue={values?.codelistA || formData.codelist0}
        handleChange={handleChange}
        name="codelistA"
      />
      <p className="max-w-prose text-lg">
        {lines[0]}
        <span className="block font-semibold py-1">{lines[1]}</span>
        {lines[2]}
        <span className="block font-semibold py-1">{endDate}</span>
        {lines[3]}
      </p>
      <SelectBox
        defaultValue={values?.codelistB || formData.codelist1}
        handleChange={handleChange}
        name="codelistB"
      />
      <p className="max-w-prose text-lg">{lines[4]}</p>
      <div className="flex flex-row gap-x-1">
        <Field
          className={classNames(
            "inline-flex w-[6ch] relative rounded-md border-gray-400 border-2 bg-white p-1 shadow-sm"
          )}
          inputMode="numeric"
          max="52"
          min="0"
          name="timeValue"
          type="text"
        />
        <Field
          as="select"
          className={classNames(
            "inline-flex w-[12ch] relative rounded-md border-gray-400 border-2 bg-white p-1 shadow-sm"
          )}
          name="timeScale"
        >
          {builderTimeScales.map(({ label, value }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Field>
        <Field
          as="select"
          className={classNames(
            "inline-flex w-[10ch] relative rounded-md border-gray-400 border-2 bg-white p-1 shadow-sm"
          )}
          name="timeEvent"
        >
          {builderTimeEvents.map(({ label, value }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Field>
      </div>
      {errors.timeValue && touched.timeValue ? (
        <InputError>Select a valid time scale</InputError>
      ) : null}
      <p className="max-w-prose text-lg">
        {values.codelistA.label || formData.codelist0?.label}
      </p>
    </div>
  );
}

export default CodelistBuilder;
