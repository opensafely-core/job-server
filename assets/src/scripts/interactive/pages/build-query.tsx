import { Form, Formik } from "formik";
import { redirect, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import CodelistBuilder from "../components/CodelistBuilder";
import FormDebug from "../components/FormDebug";
import { step1Schema } from "../data/schema";
import { useFormStore } from "../stores";
import { FormDataTypes } from "../types";

export function QueryBuilderLoader() {
  const formData = useFormStore.getState()?.formData;

  if (!formData?.codelist0 || !formData?.codelist1 || !formData?.frequency) {
    return redirect("/");
  }

  return null;
}

function QueryBuilder() {
  const navigate = useNavigate();
  const formData: FormDataTypes = useFormStore((state) => state.formData);

  return (
    <Formik
      initialValues={{
        codelistA: formData.codelistA || formData.codelist0,
        codelistB: formData.codelistB || formData.codelist1,
        timeValue: formData.timeValue || 3,
        timeScale: formData.timeScale || "weeks",
        timeEvent: formData.timeEvent || "before",
      }}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          return navigate("/preview-request");
        });
      }}
      validateOnMount
      validationSchema={step1Schema}
    >
      {({ isValid }) => (
        <Form>
          <h2 className="text-3xl font-bold mb-3">Report request</h2>
          <CodelistBuilder />
          <Button className="mt-6" disabled={!isValid} type="submit">
            Next
          </Button>

          <FormDebug />
        </Form>
      )}
    </Formik>
  );
}

export default QueryBuilder;
