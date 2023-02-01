import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { lines as multiLines } from "../components/CodelistBuilder";
import ReviewLineItem from "../components/ReviewLineItem";
import { demographics, endDate, filterPopulation } from "../data/form-fields";
import { useFormStore } from "../stores";
import { FormDataTypes } from "../types";
import { delay, requiredLoader } from "../utils";
import { lines as singleLines } from "./review-query";

export const ReviewRequestLoader = () =>
  requiredLoader({
    fields: ["codelist0", "frequency", "filterPopulation", "demographics"],
  });

function ReviewRequest() {
  const navigate = useNavigate();
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = async () => {
    setIsSubmitting(true);
    await delay(1000);
    navigate("/success");
  };

  return (
    <>
      <h1 className="text-4xl font-bold mb-6">Review your request</h1>
      <div className="mt-5 border-t border-gray-200">
        <dl className="divide-y divide-gray-200">
          {!formData.codelist1 && formData.codelist0?.label ? (
            <ReviewLineItem page="/build-query" title="Codelist">
              {formData.codelist0.label}
            </ReviewLineItem>
          ) : null}

          {formData.codelist1?.label && formData.codelist0?.label ? (
            <ReviewLineItem page="/build-query" title="Codelists">
              {formData.codelist0.label},<br />
              {formData.codelist1.label}
            </ReviewLineItem>
          ) : null}

          <ReviewLineItem page="/build-query" title="Frequency">
            {`${formData.frequency
              ?.slice(0, 1)
              .toUpperCase()}${formData.frequency?.slice(1)}`}
          </ReviewLineItem>

          {formData.codelistA?.label && formData.codelistB?.label ? (
            <ReviewLineItem page="/build-query" title="Report request">
              <span className="block font-semibold">
                {formData.codelistA.label}
              </span>
              {` ${multiLines[0]} `}
              <span className="block">
                {multiLines[1]} {multiLines[2]} {endDate}
              </span>
              {` ${multiLines[3]} `}
              <span className="block font-semibold">
                {formData.codelistB.label}
              </span>
              {` ${multiLines[4]} `}
              <span className="block">
                {formData.timeValue} {formData.timeScale} {formData.timeEvent}
              </span>
              <span className="block font-semibold">
                {` ${formData.codelistA.label}`}
              </span>
            </ReviewLineItem>
          ) : null}

          {!formData.codelist1 && formData.codelist0?.label ? (
            <ReviewLineItem page="/review-query" title="Report request">
              {`${singleLines[0]} `}
              <span className="block font-semibold">
                {formData.codelist0?.label}
              </span>
              {singleLines[1]}
              <span className="block">
                {singleLines[2]} {singleLines[3]} {endDate}.
              </span>
            </ReviewLineItem>
          ) : null}

          <ReviewLineItem page="/filter-request" title="Filter population">
            {
              filterPopulation.items.filter(
                (item) => item.value === formData.filterPopulation
              )[0].label
            }
          </ReviewLineItem>

          <ReviewLineItem
            page="/filter-request"
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
        </dl>
      </div>

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
