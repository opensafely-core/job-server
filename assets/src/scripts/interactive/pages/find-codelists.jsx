import { Form, Formik } from "formik";
import { useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import Button from "../components/Button";
import CodelistSearch from "../components/CodelistSearch";
import { useAppData, useFormData } from "../context";
import { codelistSchema } from "../data/schema";

function FindCodelists() {
  const { formData, setFormData } = useFormData();
  const { codelistGroups } = useAppData();

  const [, navigate] = useLocation();

  const validationSchema = Yup.object({
    codelist0: codelistSchema(codelistGroups),
    codelist1: codelistSchema(codelistGroups).test(
      "compare_codelists",
      "Codelists cannot be the same, please change one codelist",
      (value, testContext) => {
        if (
          Object.entries(testContext.parent.codelist0).toString() ===
          Object.entries(value).toString()
        ) {
          return false;
        }

        return true;
      },
    ),
  });

  const initialValues = {
    codelist0: formData.codelist0 || "",
    codelist1: formData.codelist1 || "",
  };

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          setFormData({
            ...formData,
            ...values,
            codelistA: null,
            codelistB: null,
          });
          return navigate("/build-query");
        });
      }}
      validateOnMount
      validationSchema={validationSchema}
    >
      {({ isValid }) => (
        <Form className="flex flex-col gap-y-12">
          <AlertForm />
          <CodelistSearch id={0} label="Select a codelist" />
          <CodelistSearch id={1} label="Select a second codelist" />

          <Button disabled={!isValid} type="submit">
            Next
          </Button>
        </Form>
      )}
    </Formik>
  );
}

export default FindCodelists;
