import { Form, Formik } from "formik";
import { useState } from "react";
import { useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import { Button } from "../components/Button";
import CodelistButton from "../components/Button/CodelistButton";
import CodelistSearch from "../components/CodelistSearch";
import Fieldset from "../components/Fieldset";
import HintText from "../components/HintText";
import InputError from "../components/InputError";
import RadioButton from "../components/RadioButton";
import { frequency } from "../data/form-fields";
import { codelistSchema } from "../data/schema";
import { useFormStore, usePageData } from "../stores";

function FindCodelists() {
  const formData = useFormStore((state) => state.formData);
  const { pageData } = usePageData.getState();
  const [secondCodelist, setSecondCodelist] = useState(!!formData.codelist1);

  const [, navigate] = useLocation();

  const validationSchema = Yup.object({
    codelist0: codelistSchema(pageData),
    codelist1: secondCodelist
      ? codelistSchema(pageData).test(
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
    frequency: Yup.string()
      .oneOf(frequency.items.map((item) => item.value))
      .required("Select a frequency"),
  });

  const initialValues = {
    codelist0: formData.codelist0 || "",
    codelist1: formData.codelist1 || undefined,
    frequency: formData.frequency || "",
  };

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          if (secondCodelist) {
            return navigate("build-query");
          }
          return navigate("review-query");
        });
      }}
      validateOnMount
      validationSchema={validationSchema}
    >
      {({ errors, isValid, touched }) => (
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

          <Fieldset legend={frequency.label}>
            <HintText>
              <p>
                This is how the data will be aggregated and shown on the report.
              </p>
              <p>
                If you are unsure, select <strong>Monthly</strong>.
              </p>
            </HintText>
            {frequency.items.map((item) => (
              <RadioButton
                key={item.value}
                id={item.value}
                label={item.label}
                name="frequency"
                value={item.value}
              />
            ))}
            {errors.frequency && touched.frequency ? (
              <InputError>{errors.frequency}</InputError>
            ) : null}
          </Fieldset>

          <Button disabled={!isValid} type="submit">
            Next
          </Button>
        </Form>
      )}
    </Formik>
  );
}

export default FindCodelists;
