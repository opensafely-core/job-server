import { Redirect, useLocation } from "wouter";
import { AlertPage } from "../components/Alert";
import { Button } from "../components/Button";
import { useAppData, useFormData } from "../context";
import { classNames, useRequiredFields } from "../utils";

export const lines = [
  "Your report will show the number of people who have had",
  "added to their health record in the period between",
  "and",
];

function ReviewQuery() {
  const [, navigate] = useLocation();
  const { formData } = useFormData();
  const {
    dates: { startStr, endStr },
  } = useAppData();

  if (useRequiredFields(["codelist0"])) {
    return <Redirect to="" />;
  }

  return (
    <>
      <AlertPage />
      <p className="max-w-prose text-xl leading-relaxed mb-4">
        {`${lines[0]} `}
        <a
          className={classNames(
            "text-oxford-600 font-bold block underline underline-offset-2 decoration-oxford-600/30"
          )}
          href={`https://www.opencodelists.org/codelist/${formData.codelist0?.value}`}
          rel="noopener noreferrer"
          target="_blank"
        >
          {formData.codelist0?.label}
        </a>
        {` ${lines[1]} `}
        <span className="block font-semibold">{startStr}</span>
        {lines[2]}
        <span className="block font-semibold">{endStr}.</span>
      </p>
      <Button
        className="mt-6"
        onClick={() => navigate("filter-request")}
        type="submit"
      >
        Next
      </Button>
    </>
  );
}

export default ReviewQuery;
