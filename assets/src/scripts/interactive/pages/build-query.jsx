import { Field, Form, Formik } from "formik";
import { Redirect, useLocation } from "wouter";
// import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import Button from "../components/Button";
import InputError from "../components/InputError";
import { SelectContainer } from "../components/Select";
import { useAppData, useFormData } from "../context";
import { builderTimeScales } from "../data/form-fields";
// import { codelistSchema } from "../data/schema";
import { classNames, useRequiredFields } from "../utils";
import { anyTimeQuery, queryText, timeQuery } from "../utils/query-text";

function timeStatement(values) {
  return `up to ${values.timeValue} ${values.timeScale} before.`;
}

function initialValues(formData) {
  return {
    codelistA: formData.codelistA || formData.codelist0,
    codelistB: formData.codelistB || formData.codelist1,
    timeOption:
      formData.timeOption === anyTimeQuery
        ? anyTimeQuery
        : timeStatement({
            timeValue: formData.timeValue || 5,
            timeScale: formData.timeScale || "years",
          }),
    timeValue: formData.timeValue || 5,
    timeScale: formData.timeScale || "years",
  };
}

function handleChange({ selectedItem, setFieldValue, values }) {
  if (selectedItem === values.codelistA) {
    setFieldValue("codelistA", values.codelistB);
    setFieldValue("codelistB", selectedItem);
  }

  if (selectedItem === values.codelistB) {
    setFieldValue("codelistB", values.codelistA);
    setFieldValue("codelistA", selectedItem);
  }
}

function QueryBuilder() {
  const [, navigate] = useLocation();
  // const { codelistGroups } = useAppData();
  const {
    dates: { startStr, endStr },
  } = useAppData();
  const { formData, setFormData } = useFormData();

  if (useRequiredFields(["codelist0", "codelist1"])) {
    return <Redirect to="" />;
  }

  // const validationSchema = Yup.object().shape({
  //   codelistA: codelistSchema(codelistGroups),
  //   codelistB: codelistSchema(codelistGroups),
  //   timeValue: Yup.number()
  //     .typeError("Amount must be a number")
  //     .positive("Time value must be a positive number")
  //     .min(1, "Time scale cannot be less than 1")
  //     .required("Amount of time is required")
  //     .test(
  //       "tenYears",
  //       "Time scale cannot be longer than 10 years",
  //       (value, testContext) => {
  //         if (value === undefined || Number.isNaN(value)) return false;

  //         const { timeScale } = testContext.parent;
  //         if (timeScale === "weeks" && value > 522) return false;
  //         if (timeScale === "months" && value > 120) return false;
  //         if (timeScale === "years" && value > 10) return false;

  //         return true;
  //       }
  //     ),
  //   timeScale: Yup.string()
  //     .oneOf(builderTimeScales.map((event) => event.value))
  //     .required(),
  // });

  return (
    <Formik
      initialValues={initialValues(formData)}
      onSubmit={(values, actions) =>
        actions.validateForm().then(() => {
          setFormData({ ...formData, ...values });
          return navigate("preview-request");
        })
      }
      validateOnBlur
      validateOnChange
      validateOnMount
      // validationSchema={validationSchema}
    >
      {({
        errors,
        isValid,
        setFieldTouched,
        setFieldValue,
        touched,
        validateField,
        values,
      }) => (
        <Form>
          <AlertForm />
          <h2 className="text-3xl font-bold mb-3">Report request</h2>

          <div className="flex flex-col gap-y-1">
            <p className="max-w-prose text-lg">{queryText[0]}</p>

            <SelectContainer
              defaultValue={values?.codelistA || values.codelist0}
              handleChange={(selectedItem) =>
                handleChange({ selectedItem, setFieldValue, values })
              }
              name="codelistA"
            />

            <p className="max-w-prose text-lg grid gap-y-1">
              {queryText[1]}
              <span>
                <strong>{startStr}</strong> {queryText[2]}{" "}
                <strong>{endStr}</strong>
              </span>
              {queryText[3]}
            </p>

            <p className="max-w-prose text-lg">
              <strong className="block mb-1">
                {values.codelistB.label || formData.codelist1?.label}
              </strong>
              {queryText[4]}{" "}
              <span className="block mt-1">
                <strong>
                  {values.codelistA.label || formData.codelist0?.label}
                </strong>{" "}
                {queryText[5]}
              </span>
            </p>

            <fieldset>
              <legend className="sr-only">Select a time scale</legend>
              <label htmlFor="timeHasValue">
                <Field
                  id="timeHasValue"
                  name="timeOption"
                  type="radio"
                  value={timeStatement(values)}
                />
                <div>
                  <span>up to</span>
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

                      setFieldTouched("timeOption");
                      setFieldValue(
                        "timeOption",
                        timeStatement({
                          timeValue: e.target.value,
                          timeScale: values.timeScale,
                        })
                      );
                    }}
                    type="text"
                  />
                  <Field
                    as="select"
                    className={classNames(
                      "inline-flex w-[12ch] relative rounded-md border-gray-400 border-2 bg-white p-1 shadow-sm"
                    )}
                    name="timeScale"
                    onChange={(e) => {
                      validateField("timeScale");
                      setFieldTouched("timeScale");
                      setFieldValue("timeScale", e.target.value);

                      setFieldTouched("timeOption");
                      setFieldValue(
                        "timeOption",
                        timeStatement({
                          timeValue: values.timeValue,
                          timeScale: e.target.value,
                        })
                      );
                    }}
                  >
                    {builderTimeScales.map(({ label, value }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </Field>
                  <span>{timeQuery}</span>
                </div>
              </label>
              <label htmlFor="anyTime">
                <Field
                  id="anyTime"
                  name="timeOption"
                  type="radio"
                  value={anyTimeQuery}
                />
                {anyTimeQuery}
              </label>
            </fieldset>

            {errors.timeValue && touched.timeValue ? (
              <InputError>{errors.timeValue}</InputError>
            ) : null}
          </div>

          <Button className="mt-6" disabled={!isValid} type="submit">
            Next
          </Button>
        </Form>
      )}
    </Formik>
  );
}

export default QueryBuilder;
