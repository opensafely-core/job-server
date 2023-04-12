import { Form, Formik } from "formik";
import { Redirect, useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import Button from "../components/Button";
import InputError from "../components/InputError";
import Textarea from "../components/Textarea";
import { useFormData } from "../context";
import { useRequiredFields } from "../utils";

function Purpose() {
  const [, navigate] = useLocation();
  const { formData, setFormData } = useFormData();

  if (
    useRequiredFields([
      "codelistA",
      "codelistB",
      "timeScale",
      "timeValue",
      "filterPopulation",
    ])
  ) {
    return <Redirect to="" />;
  }

  const validationSchema = Yup.object().shape({
    purpose: Yup.string().required("Write a purpose for this analysis"),
    title: Yup.string().required("Write a title for this analysis"),
  });

  const initialValues = {
    purpose: formData.purpose || "",
    title: formData.title || "",
  };

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          setFormData({ ...formData, ...values });
          navigate("review-request");
        });
      }}
      validateOnMount
      validationSchema={validationSchema}
    >
      {({ errors, isValid, touched }) => (
        <Form className="flex flex-col gap-y-4">
          <AlertForm />
          <h1 className="text-4xl font-bold">Analysis information</h1>

          <Textarea
            characterCount
            className="mb-6"
            hintText="We should provide some text here to explain"
            id="title"
            label="Provide a title for the analysis"
            maxlength={60}
            name="title"
            required
            resize={false}
            rows={2}
          />

          {errors.title && touched.title ? (
            <InputError>{errors.title}</InputError>
          ) : null}

          <Textarea
            characterCount
            id="purpose"
            label="Describe the purpose of this analysis"
            maxlength={1000}
            name="purpose"
            required
            resize={false}
          />
          {errors.purpose && touched.purpose ? (
            <InputError>{errors.purpose}</InputError>
          ) : null}

          <div className="flex flex-row w-full gap-2 mt-4">
            <Button disabled={!isValid} type="submit">
              Next
            </Button>
          </div>
        </Form>
      )}
    </Formik>
  );
}

export default Purpose;
