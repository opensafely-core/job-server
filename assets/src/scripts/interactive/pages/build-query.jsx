import { Form, Formik } from "formik";
import { Redirect, useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import Button from "../components/Button";
import QueryBuilder from "../components/QueryBuilder";
import { useAppData, useFormData } from "../context";
import { builderTimeScales } from "../data/form-fields";
import { codelistSchema } from "../data/schema";
import { useRequiredFields } from "../utils";
import { anyTimeQuery, timeStatement } from "../utils/query-text";

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

function BuildQuery() {
  const [, navigate] = useLocation();
  const { codelistGroups } = useAppData();
  const { formData, setFormData } = useFormData();

  if (useRequiredFields(["codelist0", "codelist1"])) {
    return <Redirect to="" />;
  }

  const validationSchema = Yup.object().shape({
    codelistA: codelistSchema(codelistGroups),
    codelistB: codelistSchema(codelistGroups),
    timeOption: Yup.string().required(),
    timeValue: Yup.number()
      .typeError("Amount must be a number")
      .positive("Time value must be a positive number")
      .min(1, "Time scale cannot be less than 1")
      .required("Amount of time is required")
      .test(
        "tenYears",
        "Time scale cannot be longer than 10 years",
        (value, testContext) => {
          const { timeScale, timeOption } = testContext.parent;
          if (timeOption === anyTimeQuery) return true;

          if (value === undefined || Number.isNaN(value)) return false;

          if (timeScale === "weeks" && value > 522) return false;
          if (timeScale === "months" && value > 120) return false;
          if (timeScale === "years" && value > 10) return false;

          return true;
        }
      ),
    timeScale: Yup.string()
      .oneOf(builderTimeScales.map((event) => event.value))
      .required(),
  });

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
      validationSchema={validationSchema}
    >
      {({ isValid }) => (
        <Form>
          <AlertForm />
          <h2 className="text-3xl font-bold mb-3">Report request</h2>

          <QueryBuilder />

          <Button className="mt-6" disabled={!isValid} type="submit">
            Next
          </Button>
        </Form>
      )}
    </Formik>
  );
}

export default BuildQuery;
