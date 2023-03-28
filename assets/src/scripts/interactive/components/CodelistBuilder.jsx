import { Field, useFormikContext } from "formik";
import { useAppData, useFormData } from "../context";
import { builderTimeScales } from "../data/form-fields";
import { classNames } from "../utils";
import InputError from "./InputError";
import { SelectContainer } from "./Select";

export const lines = [
  "added to their health record in the period between",
  "and",
  "who have also had",
  "added to their health record from",
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
      <p className="max-w-prose text-lg">The number of people who had</p>
      <SelectContainer
        defaultValue={values?.codelistA || formData.codelist0}
        handleChange={handleChange}
        name="codelistA"
      />
      <p className="max-w-prose text-lg">
        {lines[0]}
        <span className="block">
          <strong>{startStr}</strong> {lines[1]} <strong>{endStr}</strong>
        </span>
        {lines[2]}
      </p>
      <SelectContainer
        defaultValue={values?.codelistB || formData.codelist1}
        handleChange={handleChange}
        name="codelistB"
      />
      <p className="max-w-prose text-lg">{lines[3]}</p>
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
      <p className="max-w-prose text-lg">
        before {values.codelistA.label || formData.codelist0?.label}.
      </p>
    </div>
  );
}

export default CodelistBuilder;
