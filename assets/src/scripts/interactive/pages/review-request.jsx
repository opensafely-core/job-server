import { useState } from "react";
import { Redirect } from "wouter";
import { AlertPage, removeAlert } from "../components/Alert";
import Button from "../components/Button";
import InputError from "../components/InputError";
import ReviewLineItem from "../components/ReviewLineItem";
import { useAppData, useFormData } from "../context";
import { demographics, filterPopulation } from "../data/form-fields";
import { removeUndefinedValuesFromObject, useRequiredFields } from "../utils";
import { anyTimeQuery, queryText, timeQuery } from "../utils/query-text";

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
      "timeOption",
      "filterPopulation",
      "title",
      "purpose",
    ])
  ) {
    return <Redirect to="" />;
  }

  const dataForSubmission = () => {
    const {
      codelistA,
      timeOption,
      timeScale,
      timeValue,
      filterPopulation: filterOpts,
      demographics: demographicOpts,
      title,
      purpose,
    } = formData;

    return removeUndefinedValuesFromObject({
      codelistA: {
        label: codelistA.label,
        type: codelistA.type,
        value: codelistA.value,
      },
      codelistB: {
        label: codelistA.label,
        type: codelistA.type,
        value: codelistA.value,
      },

      startDate: startISO.slice(0, 10),
      endDate: endISO.slice(0, 10),

      timeEver: timeOption === anyTimeQuery ? "true" : null,
      timeScale: timeOption === anyTimeQuery ? undefined : timeScale,
      timeValue: timeOption === anyTimeQuery ? undefined : timeValue,

      filterPopulation: filterOpts,
      demographics: demographicOpts,

      title,
      purpose,
    });
  };

  const handleClick = async () => {
    setIsSubmitting(true);
    setError("");
    console.log(dataForSubmission());
    setIsSubmitting(false);

    // const response = await fetch(`${basePath}publish`, {
    //   method: "POST",
    //   headers: {
    //     "Content-Type": "application/json",
    //     "X-CSRFToken": csrfToken,
    //   },
    //   body: JSON.stringify(dataForSubmission()),
    // });

    // if (!response.ok) {
    //   setIsSubmitting(false);
    //   const message = `An error has occured: ${response.status} - ${response.statusText}`;
    //   setError(message);
    //   throw new Error(message);
    // }

    // removeAlert();
    // window.location.href = response.url;
  };

  const timeStatement =
    formData.timeOption === anyTimeQuery
      ? anyTimeQuery
      : `up to ${formData.timeValue} ${formData.timeScale} ${timeQuery}`;

  return (
    <>
      <AlertPage />
      <h2 className="text-4xl font-bold mb-6">Review your request</h2>
      <div className="mt-5 border-t border-gray-200">
        <dl className="divide-y divide-gray-200">
          <ReviewLineItem page="find-codelists" title="Codelists">
            {formData.codelist0?.label},<br />
            {formData.codelist1?.label}
          </ReviewLineItem>

          {formData.codelistA?.label && formData.codelistB?.label ? (
            <ReviewLineItem page="build-query" title="Report request">
              {` ${queryText[0]} `}
              <strong>{formData.codelistA.label}</strong>
              {` ${queryText[1]} `}
              <strong>{startStr}</strong> {queryText[2]}{" "}
              <strong>{endStr}</strong>
              {` ${queryText[3]} `}
              <strong>{formData.codelistB.label}</strong>
              {` ${queryText[4]} `}
              <strong>{` ${formData.codelistA.label}`}</strong>
              {` ${queryText[5]} ${timeStatement}`}
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
            {formData.demographics.length ? (
              <ul>
                {formData.demographics?.map((selected) => (
                  <li key={selected}>
                    {
                      demographics.items.find((a) => a?.value === selected)
                        ?.label
                    }
                  </li>
                ))}
              </ul>
            ) : (
              <p>No demographics selected</p>
            )}
          </ReviewLineItem>

          <ReviewLineItem
            page="analysis-information"
            title="Analysis information"
          >
            <p className="mb-4">
              <strong>Title: </strong>
              <br />
              {formData.title}
            </p>
            <p>
              <strong>Description: </strong>
              <br />
              {formData.purpose}
            </p>
          </ReviewLineItem>
        </dl>
      </div>

      {error ? <InputError>{error}</InputError> : null}

      <section className="prose prose-blue mt-8 pt-6 border-t max-w-full">
        <h2 className="sr-only">Read and agree</h2>
        <ul>
          <li>
            Your analyses will be run on primary care patient records for
            approximately 44% of the English population
          </li>
          <li>
            The analysis you are requesting may take up to 5 days to return
            results
          </li>
          <li>
            The time for the analysis to generate may vary significantly
            dependent on current loads on our servers and current demand for our
            disclosure checking service
          </li>
          {/* <li>
            If you want to check what the report will look like prior to running
            this analysis, you can see an example here [link]
          </li> */}
          <p>By making this request you are agreeing:</p>
          <ul>
            <li>
              That your request falls within your approved project purpose
            </li>
            <li>To abide by the Terms and Conditions you signed previously</li>
            <li>
              That the contents of this request, along with your name and email
              address, will be publicly available
            </li>
          </ul>
        </ul>
      </section>

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
