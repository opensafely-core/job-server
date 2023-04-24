import { Form, Formik } from "formik";
import { Redirect, useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import Button from "../components/Button";
import InputError from "../components/InputError";
import Textarea from "../components/Textarea";
import { useFormData } from "../context";
import { useRequiredFields } from "../utils";

function AnalysisInformation() {
  const [, navigate] = useLocation();
  const { formData, setFormData } = useFormData();

  if (
    useRequiredFields([
      "codelistA",
      "codelistB",
      "timeOption",
      "filterPopulation",
    ])
  ) {
    return <Redirect to="" />;
  }

  const validationSchema = Yup.object().shape({
    purpose: Yup.string()
      .required("Write a purpose for this analysis")
      .min(1, "Add a purpose")
      .max(1000, "Purpose is too long"),
    title: Yup.string()
      .required("Write a title for this analysis")
      .min(1, "Add a title")
      .max(140, "Title is too long"),
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
            hintText={
              <>
                <p>
                  The title will be shown at the top of the generated report. It
                  should provide a short summary to anyone reading the report
                  about what the analysis shows.
                </p>
                <p>
                  You will be able to change this after the report is generated.
                </p>
              </>
            }
            id="title"
            label="Provide a title for the analysis"
            maxlength={140}
            name="title"
            placeholder=""
            required
            resize={false}
            rows={2}
            value={`${formData.codelistA.label} & ${formData.codelistB.label} during the COVID-19 pandemic`}
          >
            {errors.title && touched.title ? (
              <InputError>{errors.title}</InputError>
            ) : null}
          </Textarea>

          <Textarea
            characterCount
            hintText={
              <>
                <p>
                  It must be clear that this analysis request is aligned with
                  your approvals.
                </p>
                <p>
                  Please refer to the approved version of your project
                  application form, which you were sent by email.
                </p>
              </>
            }
            id="purpose"
            label="Explain why this analysis fits with the approved project purpose"
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

export default AnalysisInformation;
