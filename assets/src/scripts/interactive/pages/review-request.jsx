import { useState } from "react";
import { Redirect } from "wouter";
import { AlertPage, removeAlert } from "../components/Alert";
import Button from "../components/Button";
import { lines as multiLines } from "../components/CodelistBuilder";
import InputError from "../components/InputError";
import ReviewLineItem from "../components/ReviewLineItem";
import { useAppData, useFormData } from "../context";
import { demographics, filterPopulation } from "../data/form-fields";
import { useRequiredFields } from "../utils";

function ReviewRequest() {
  const {
    basePath,
    csrfToken,
    dates: { startISO, endISO, startStr, endStr },
  } = useAppData();
  const { formData } = useFormData();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (
    useRequiredFields([
      "codelistA",
      "codelistB",
      "timeScale",
      "timeValue",
      "filterPopulation",
      "demographics",
      "purpose",
    ])
  ) {
    return <Redirect to="" />;
  }

  const dataForSubmission = () => {
    const { codelist0, codelist1, codelistA, codelistB, ...data } = formData;

    return {
      ...data,
      title: `${codelistA?.label} & ${codelistB?.label}`,
      codelistA: {
        label: codelistA?.label,
        type: codelistA?.type,
        value: codelistA?.value,
      },
      codelistB: {
        label: codelistB?.label,
        type: codelistB?.type,
        value: codelistB?.value,
      },
      startDate: startISO.slice(0, 10),
      endDate: endISO.slice(0, 10),
    };
  };

  const handleClick = async () => {
    setIsSubmitting(true);
    setError("");

    const response = await fetch(`${basePath}publish`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(dataForSubmission()),
    });

    if (!response.ok) {
      setIsSubmitting(false);
      const message = `An error has occured: ${response.status} - ${response.statusText}`;
      setError(message);
      throw new Error(message);
    }

    removeAlert();
    window.location.href = response.url;
  };

  return (
    <>
      <AlertPage />
      <h1 className="text-4xl font-bold mb-6">Review your request</h1>
      <div className="mt-5 border-t border-gray-200">
        <dl className="divide-y divide-gray-200">
          <ReviewLineItem page="" title="Codelists">
            {formData.codelist0?.label},<br />
            {formData.codelist1?.label}
          </ReviewLineItem>

          {formData.codelistA?.label && formData.codelistB?.label ? (
            <ReviewLineItem page="build-query" title="Report request">
              {` ${multiLines[0]} `}
              <strong>{formData.codelistA.label}</strong>
              {` ${multiLines[1]} `}
              <strong>{startStr}</strong> {multiLines[2]}{" "}
              <strong>{endStr}</strong>
              {` ${multiLines[3]} `}
              <strong>{formData.codelistB.label}</strong>
              {` ${multiLines[4]} `}
              <strong>{` ${formData.codelistA.label}`}</strong>
              {` ${multiLines[5]} `}
              {formData.timeValue} {formData.timeScale}
              {` ${multiLines[6]} `}
            </ReviewLineItem>
          ) : null}

          <ReviewLineItem page="filter-request" title="Filter population">
            {
              filterPopulation.items.filter(
                (item) => item.value === formData.filterPopulation
              )[0].label
            }
          </ReviewLineItem>

          <ReviewLineItem
            page="filter-request"
            title="Break down the report by demographics"
          >
            <ul>
              {formData.demographics?.map((selected) => (
                <li key={selected}>
                  {demographics.items.find((a) => a?.value === selected)?.label}
                </li>
              ))}
            </ul>
          </ReviewLineItem>

          <ReviewLineItem page="purpose" title="Purpose of this analysis">
            <p>{formData.purpose}</p>
          </ReviewLineItem>
        </dl>
      </div>

      {error ? <InputError>{error}</InputError> : null}

      <div className="flex flex-row w-full gap-2 mt-10">
        <Button disabled={isSubmitting} onClick={handleClick} type="submit">
          {isSubmitting ? (
            <>
              <svg
                className="h-5 w-5 flex-1 animate-spin stroke-current stroke-[3] mr-2"
                fill="none"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  className="stroke-current opacity-25"
                  d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
                />
                <path d="M12 2C6.47715 2 2 6.47715 2 12C2 14.7255 3.09032 17.1962 4.85857 19" />
              </svg>
              Submitting
            </>
          ) : (
            "Submit request"
          )}
        </Button>
      </div>
    </>
  );
}

export default ReviewRequest;
