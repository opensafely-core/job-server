import { Field, useFormikContext } from "formik";
import { useAppData, useFormData } from "../context";
import { builderTimeScales } from "../data/form-fields";
import { classNames } from "../utils";
import InputError from "./InputError";
import { SelectContainer } from "./Select";

export const lines = [
  "The number of people who had",
  "added to their health record each month from",
  "to",
  "who have also had",
  "added to their health record in the same month as",
  "or up to",
  "before the start of that month.",
];

function CodelistBuilder() {
  const { formData } = useFormData();
  const {
    dates: { startStr, endStr },
  } = useAppData();
  const {
    values,
    setFieldValue,
    errors,
    touched,
    validateField,
    setFieldTouched,
  } = useFormikContext();

  const handleChange = (selectedItem) => {
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
      <p className="max-w-prose text-lg">{lines[0]}</p>
      <SelectContainer
        defaultValue={values?.codelistA || formData.codelist0}
        handleChange={handleChange}
        name="codelistA"
      />
      <p className="max-w-prose text-lg grid gap-y-2">
        {lines[1]}
        <span>
          <strong>{startStr}</strong> {lines[2]} <strong>{endStr}</strong>
        </span>
        {lines[3]}
      </p>
      <SelectContainer
        defaultValue={values?.codelistB || formData.codelist1}
        handleChange={handleChange}
        name="codelistB"
      />
      <p className="max-w-prose text-lg grid gap-y-2">
        {lines[4]}{" "}
        <strong>{values.codelistA.label || formData.codelist0?.label}</strong>{" "}
        {lines[5]}
      </p>
      <div className="flex flex-row gap-x-1">
        <Field
          className={classNames(
            "inline-flex w-[6ch] relative rounded-md border-gray-400 border-2 bg-white p-1 shadow-sm"
          )}
          inputMode="numeric"
          max="52"
          min="0"
          name="timeValue"
          onChange={(e) => {
            validateField("timeValue");
            setFieldTouched("timeValue");
            setFieldValue("timeValue", e.target.value);
          }}
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
      </div>
      {errors.timeValue && touched.timeValue ? (
        <InputError>{errors.timeValue}</InputError>
      ) : null}
      <p className="max-w-prose text-lg">{lines[6]}</p>
    </div>
  );
}

export default CodelistBuilder;
