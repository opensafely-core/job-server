import { redirect, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { endDate } from "../data/form-fields";
import { useFormStore } from "../stores";
import { FormDataTypes } from "../types";
import { classNames } from "../utils";

export function ReviewQueryLoader() {
  const formData = useFormStore.getState()?.formData;

  if (!formData?.codelist0 || !formData?.frequency) {
    return redirect("/");
  }

  return null;
}

export const lines = [
  "Your report will show the number of people who have had",
  "added to their health record in the period between",
  "1st September 2019",
  "and",
];

function ReviewQuery() {
  const navigate = useNavigate();
  const formData: FormDataTypes = useFormStore((state) => state.formData);

  return (
    <>
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
        onClick={() => navigate("/filter-request")}
        type="submit"
      >
        Next
      </Button>
    </>
  );
}

export default ReviewQuery;
