import { Form, Formik } from "formik";
import { Redirect, useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import { Button } from "../components/Button";
import CodelistBuilder from "../components/CodelistBuilder";
import { useAppData, useFormData } from "../context";
import { builderTimeEvents, builderTimeScales } from "../data/form-fields";
import { codelistSchema } from "../data/schema";
import { useRequiredFields } from "../utils";

function QueryBuilder() {
  const [, navigate] = useLocation();
  const { codelistGroups } = useAppData();
  const { formData, setFormData } = useFormData();

  if (useRequiredFields(["codelist0", "codelist1"])) {
    return <Redirect to="" />;
  }

  const validationSchema = Yup.object().shape({
    codelistA: codelistSchema(codelistGroups),
    codelistB: codelistSchema(codelistGroups),
    timeValue: Yup.number()
      .positive()
      .min(1)
      .max(260, "Time scale cannot be longer than 5 years")
      .required()
      .test(
        "fiveYears",
        "Time scale cannot be longer than 5 years",
        (value, testContext) => {
          if (value === undefined || Number.isNaN(value)) return false;

          const { timeScale } = testContext.parent;
          if (timeScale === "weeks" && value > 260) return false;
          if (timeScale === "months" && value > 60) return false;
          if (timeScale === "years" && value > 5) return false;

          return true;
        }
      ),
    timeScale: Yup.string()
      .oneOf(builderTimeScales.map((event) => event.value))
      .required(),
    timeEvent: Yup.string()
      .oneOf(builderTimeEvents.map((event) => event.value))
      .required(),
  });

  const initialValues = {
    codelistA: formData.codelistA || formData.codelist0,
    codelistB: formData.codelistB || formData.codelist1,
    timeValue: formData.timeValue || 3,
    timeScale: formData.timeScale || "weeks",
    timeEvent: formData.timeEvent || "before",
  };

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          setFormData({ ...formData, ...values });
          return navigate("preview-request");
        });
      }}
      validateOnMount
      validationSchema={validationSchema}
    >
      {({ isValid }) => (
        <Form>
          <AlertForm />
          <h2 className="text-3xl font-bold mb-3">Report request</h2>
          <CodelistBuilder />
          <Button className="mt-6" disabled={!isValid} type="submit">
            Next
          </Button>
        </Form>
      )}
    </Formik>
  );
}

export default QueryBuilder;
