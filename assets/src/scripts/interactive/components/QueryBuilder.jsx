import { Field, useFormikContext } from "formik";
import { useAppData, useFormData } from "../context";
import { builderTimeScales } from "../data/form-fields";
import {
  anyTimeQuery,
  queryText,
  timeQuery,
  timeStatement,
} from "../utils/query-text";
import Fieldset from "./Fieldset";
import InputError from "./InputError";
import RadioButton from "./RadioButton";
import { SelectContainer } from "./Select";

function QueryBuilder() {
  const {
    dates: { startStr, endStr },
  } = useAppData();
  const { formData } = useFormData();
  const {
    errors,
    setFieldTouched,
    setFieldValue,
    touched,
    validateField,
    values,
  } = useFormikContext();

  function handleCodelistSwap(item) {
    if (item === values.codelistA) {
      setFieldValue("codelistA", values.codelistB);
      setFieldValue("codelistB", item);
    }

    if (item === values.codelistB) {
      setFieldValue("codelistB", values.codelistA);
      setFieldValue("codelistA", item);
    }
  }

  /**
   * Pass the event and the element to change, and the other element which
   * should stay the same.
   *
   * @param {Event} event
   * @param {String} el
   * @param {String} otherEl
   * @returns {null}
   */
  function handleTimeChange(event, el, otherEl) {
    validateField(el);
    setFieldTouched(el);
    setFieldValue(el, event.target.value);

    setFieldTouched("timeOption");
    setFieldValue(
      "timeOption",
      timeStatement({
        [el]: event.target.value,
        [otherEl]: values?.[otherEl],
      })
    );
  }

  return (
    <div className="flex flex-col gap-y-1">
      <p className="max-w-prose text-lg">{queryText[0]}</p>

      <SelectContainer
        defaultValue={values?.codelistA || values.codelist0}
        handleChange={(item) => handleCodelistSwap(item)}
        name="codelistA"
      />

      <p className="max-w-prose text-lg grid gap-y-1">
        {queryText[1]}
        <span>
          <strong>{startStr}</strong> {queryText[2]} <strong>{endStr}</strong>
        </span>
        {queryText[3]}
      </p>

      <p className="max-w-prose text-lg">
        <strong className="block mb-1">
          {values.codelistB.label || formData.codelist1?.label}
        </strong>
        {queryText[4]}{" "}
        <span className="block mt-1">
          <strong>{values.codelistA.label || formData.codelist0?.label}</strong>{" "}
          {queryText[5]}
        </span>
      </p>

      <Fieldset hideLegend legend="Select a time scale">
        <RadioButton
          id="timeHasValue"
          label={timeStatement(values)}
          labelClassName="flex flex-row gap-1 items-center mt-2"
          name="timeOption"
          type="radio"
          value={timeStatement(values)}
        >
          up to
          <Field
            className="inline-flex w-[6ch] relative rounded-md border-gray-400 border-2 bg-white p-1 shadow-sm"
            inputMode="numeric"
            max="52"
            min="0"
            name="timeValue"
            onChange={(e) => handleTimeChange(e, "timeValue", "timeScale")}
            type="text"
          />
          <Field
            as="select"
            className="inline-flex w-[12ch] relative rounded-md border-gray-400 border-2 bg-white p-1 shadow-sm"
            name="timeScale"
            onChange={(e) => handleTimeChange(e, "timeScale", "timeValue")}
          >
            {builderTimeScales.map(({ label, value }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Field>
          {timeQuery}
        </RadioButton>

        <RadioButton
          id="anyTime"
          label={anyTimeQuery}
          name="timeOption"
          type="radio"
          value={anyTimeQuery}
        />
      </Fieldset>

      {errors.timeValue && touched.timeValue ? (
        <InputError>{errors.timeValue}</InputError>
      ) : null}
    </div>
  );
}

export default QueryBuilder;
