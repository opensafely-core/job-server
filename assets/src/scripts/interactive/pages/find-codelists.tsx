import { Form, Formik } from "formik";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as Yup from "yup";
import { Button } from "../components/Button";
import CodelistButton from "../components/Button/CodelistButton";
import CodelistSearch from "../components/CodelistSearch";
import Fieldset from "../components/Fieldset";
import FormDebug from "../components/FormDebug";
import InputError from "../components/InputError";
import RadioButton from "../components/RadioButton";
import { frequency } from "../data/form-fields";
import { codelistSchema } from "../data/schema";
import { useFormStore } from "../stores";
import { FormDataTypes } from "../types";

const validationSchema = (secondCodelist: Boolean) =>
  Yup.lazy(() =>
    Yup.object({
      codelist0: codelistSchema(),
      codelist1: secondCodelist
        ? codelistSchema().test(
            "compare_codelists",
            "Codelists cannot be the same, please change one codelist",
            (value: string, testContext: Yup.TestContext) => {
              if (
                Object.entries(testContext.parent.codelist0).toString() ===
                Object.entries(value).toString()
              ) {
                return false;
              }

              return true;
            }
          )
        : undefined,
      frequency: Yup.string()
        .oneOf(frequency.items.map((item) => item.value))
        .required("Select a frequency"),
    })
  );

function FindCodelists() {
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const [secondCodelist, setSecondCodelist]: [boolean, Function] = useState(
    !!formData.codelist1
  );
  const navigate = useNavigate();

  return (
    <Formik
      initialValues={{
        codelist0: formData.codelist0 || "",
        codelist1: formData.codelist1 || undefined,
        frequency: formData.frequency || "",
      }}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          if (secondCodelist) {
            return navigate("/build-query");
          }
          return navigate("/review-query");
        });
      }}
      validateOnMount
      validationSchema={validationSchema(secondCodelist)}
    >
      {({ errors, isValid, touched }) => (
        <Form>
          <CodelistSearch id={0} label="Select a codelist" />

          {secondCodelist ? (
            <CodelistSearch id={1} label="Select another codelist" />
          ) : null}

          <CodelistButton
            secondCodelist={secondCodelist}
            setSecondCodelist={setSecondCodelist}
          />

          <Fieldset legend={frequency.label} name="frequency">
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

          <Button className="mt-6" disabled={!isValid} type="submit">
            Next
          </Button>

          <FormDebug />
        </Form>
      )}
    </Formik>
  );
}

export default FindCodelists;
