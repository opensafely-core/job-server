import { Form, Formik } from "formik";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import Checkbox from "../components/Checkbox";
import Fieldset from "../components/Fieldset";
import FormDebug from "../components/FormDebug";
import InputError from "../components/InputError";
import RadioButton from "../components/RadioButton";
import { demographics, filterPopulation } from "../data/form-fields";
import { step3Schema } from "../data/schema";
import { useFormStore } from "../stores";
import { FormDataTypes } from "../types";
import { requiredLoader } from "../utils";

export const FilterRequestLoader = () =>
  requiredLoader({
    fields: ["codelist0", "frequency"],
  });

function FilterRequest() {
  const navigate = useNavigate();
  const formData: FormDataTypes = useFormStore((state) => state.formData);

  return (
    <Formik
      initialValues={{
        filterPopulation: formData.filterPopulation || "",
        demographics: formData.demographics || [],
      }}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          navigate("/review-request");
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

export default FilterRequest;
