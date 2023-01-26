import { Form, Formik } from "formik";
import { useState } from "react";
import { useWizard } from "react-use-wizard";
import { frequency } from "../../data/form-fields";
import { step0Schema } from "../../data/schema";
import { FormDataTypes, useFormStore } from "../../stores/form";
import { scrollToTop } from "../../utils";
import { Button } from "../Button";
import CodelistButton from "../Button/CodelistButton";
import CodelistSearch from "../CodelistSearch";
import Fieldset from "../Fieldset";
import FormDebug from "../FormDebug";
import InputError from "../InputError";
import RadioButton from "../RadioButton";

function Step1() {
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const [secondCodelist, setSecondCodelist]: [boolean, Function] = useState(
    !!formData.codelist1
  );
  const { handleStep, nextStep } = useWizard();

  handleStep(() => scrollToTop());

  return (
    <Formik
      initialValues={{
        codelist0: formData.codelist0 || "",
        codelist1: formData.codelist1 || "",
        frequency: formData.frequency || "",
      }}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          nextStep();
        });
      }}
      validateOnMount
      validationSchema={step0Schema(secondCodelist)}
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

export default Step1;
