import { Form, Formik } from "formik";
import { useWizard } from "react-use-wizard";
import { step1Schema } from "../../data/schema";
import { FormDataTypes, useFormStore } from "../../stores/form";
import { scrollToTop } from "../../utils";
import { Button } from "../Button";
import CodelistBuilder from "../CodelistBuilder";
import CodelistSingle from "../CodelistSingle";
import FormDebug from "../FormDebug";

function Step2() {
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const { goToStep, handleStep, nextStep } = useWizard();

  handleStep(() => scrollToTop());

  return (
    <Formik
      initialValues={
        formData.codelist1
          ? {
              codelistA: formData.codelistA || formData.codelist0,
              codelistB: formData.codelistB || formData.codelist1,
              timeValue: formData.timeValue || 3,
              timeScale: formData.timeScale || "weeks",
              timeEvent: formData.timeEvent || "before",
            }
          : {}
      }
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          if (formData.codelist1) {
            return nextStep();
          }
          return goToStep(3);
        });
      }}
      validateOnMount
      validationSchema={formData.codelist1 ? step1Schema : null}
    >
      {({ isValid }) => (
        <Form>
          <h2 className="text-3xl font-bold mb-3">Report request</h2>
          {formData.codelist1 ? <CodelistBuilder /> : <CodelistSingle />}
          <Button className="mt-6" disabled={!isValid} type="submit">
            Next
          </Button>

          <FormDebug />
        </Form>
      )}
    </Formik>
  );
}

export default Step2;
