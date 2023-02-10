import { useLocation, Redirect } from "wouter";
import { AlertPage } from "../components/Alert";
import { Button } from "../components/Button";
import { endDate } from "../data/form-fields";
import { useFormStore } from "../stores";
import { FormDataTypes } from "../types";
import { classNames, requiredLoader } from "../utils";

export const lines = [
  "Your report will show the number of people who have had",
  "added to their health record in the period between",
  "1st September 2019",
  "and",
];

function ReviewQuery() {
  const [, navigate] = useLocation();
  const formData: FormDataTypes = useFormStore((state) => state.formData);

  if (requiredLoader({ fields: ["codelist0", "frequency"] })) {
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
        <span className="block font-semibold">{lines[2]}</span>
        {lines[3]}
        <span className="block font-semibold">{endDate}.</span>
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
