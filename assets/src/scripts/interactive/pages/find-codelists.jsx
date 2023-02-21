import { Form, Formik } from "formik";
import { useState } from "react";
import { useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import { Button } from "../components/Button";
import CodelistButton from "../components/Button/CodelistButton";
import CodelistSearch from "../components/CodelistSearch";
import { useAppData, useFormData } from "../context";
import { codelistSchema } from "../data/schema";

function FindCodelists() {
  const { formData, setFormData } = useFormData();
  const { codelistGroups } = useAppData();
  const [secondCodelist, setSecondCodelist] = useState(!!formData.codelist1);

  const [, navigate] = useLocation();

  const validationSchema = Yup.object({
    codelist0: codelistSchema(codelistGroups),
    codelist1: secondCodelist
      ? codelistSchema(codelistGroups).test(
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
          }
        )
      : Yup.mixed().nullable(),
  });

  const initialValues = {
    codelist0: formData.codelist0 || "",
    codelist1: formData.codelist1 || undefined,
  };

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          setFormData({ ...formData, ...values });
          if (secondCodelist) {
            return navigate("build-query");
          }
          return navigate("review-query");
        });
      }}
      validateOnMount
      validationSchema={validationSchema}
    >
      {({ isValid }) => (
        <Form className="flex flex-col gap-y-8">
          <AlertForm />
          <CodelistSearch id={0} label="Select a codelist" />

          {secondCodelist ? (
            <CodelistSearch id={1} label="Select another codelist" />
          ) : null}

          <CodelistButton
            secondCodelist={secondCodelist}
            setSecondCodelist={setSecondCodelist}
          />

          <Button disabled={!isValid} type="submit">
            Next
          </Button>
        </Form>
      )}
    </Formik>
  );
}

export default FindCodelists;
