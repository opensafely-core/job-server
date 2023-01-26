import { Form, Formik } from "formik";
import { useWizard } from "react-use-wizard";
import { demographics, filterPopulation } from "../../data/form-fields";
import { step3Schema } from "../../data/schema";
import { FormDataTypes, useFormStore } from "../../stores/form";
import { scrollToTop } from "../../utils";
import { Button } from "../Button";
import Checkbox from "../Checkbox";
import Fieldset from "../Fieldset";
import FormDebug from "../FormDebug";
import InputError from "../InputError";
import RadioButton from "../RadioButton";

function Step4() {
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const { handleStep, nextStep } = useWizard();

  handleStep(() => scrollToTop());

  return (
    <Formik
      initialValues={{
        filterPopulation: formData.filterPopulation || "",
        demographics: formData.demographics || [],
      }}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          nextStep();
        });
      }}
      validateOnMount
      validationSchema={step3Schema}
    >
      {({ errors, isValid, touched }) => (
        <Form>
          <h1 className="text-4xl font-bold mb-4">Set report filters</h1>

          <Fieldset legend={filterPopulation.label} name="filterPopulation">
            {filterPopulation.items.map((item) => (
              <RadioButton
                key={item.value}
                id={item.value}
                label={item.label}
                name="filterPopulation"
                value={item.value}
              />
            ))}
            {errors.filterPopulation && touched.filterPopulation ? (
              <InputError>{errors.filterPopulation}</InputError>
            ) : null}
          </Fieldset>

          <Fieldset legend={demographics.label} name="demographics">
            {demographics.items.map((item) => (
              <Checkbox
                key={item.value}
                id={item.value}
                label={item.label}
                name="demographics"
                value={item.value}
              />
            ))}
            {errors.demographics && touched.demographics ? (
              <InputError>Select one or more demographics</InputError>
            ) : null}
          </Fieldset>

          <div className="flex flex-row w-full gap-2 mt-10">
            <Button className="mt-6" disabled={!isValid} type="submit">
              Next
            </Button>
          </div>

          <FormDebug />
        </Form>
      )}
    </Formik>
  );
}

export default Step4;
