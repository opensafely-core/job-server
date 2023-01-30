import { useState } from "react";
import { useWizard } from "react-use-wizard";
import {
  demographics,
  endDate,
  filterPopulation,
} from "../../data/form-fields";
import { useFormStore } from "../../stores";
import { FormDataTypes } from "../../types";
import { delay, scrollToTop } from "../../utils";
import { Button } from "../Button";
import { lines as multiLines } from "../CodelistBuilder";
import { lines as singleLines } from "../CodelistSingle";
import ReviewLineItem from "../ReviewLineItem";

function Step5() {
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const { handleStep, nextStep } = useWizard();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = async () => {
    setIsSubmitting(true);
    await delay(1000);
    nextStep();
  };

  handleStep(() => scrollToTop());

  return (
    <>
      <h1 className="text-4xl font-bold mb-6">Review your request</h1>
      <div className="mt-5 border-t border-gray-200">
        <dl className="divide-y divide-gray-200">
          {!formData.codelist1 && formData.codelist0?.label ? (
            <ReviewLineItem step={0} title="Codelist">
              {formData.codelist0.label}
            </ReviewLineItem>
          ) : null}

          {formData.codelist1?.label && formData.codelist0?.label ? (
            <ReviewLineItem step={0} title="Codelists">
              {formData.codelist0.label},<br />
              {formData.codelist1.label}
            </ReviewLineItem>
          ) : null}

          <ReviewLineItem step={0} title="Frequency">
            {`${formData.frequency
              ?.slice(0, 1)
              .toUpperCase()}${formData.frequency?.slice(1)}`}
          </ReviewLineItem>

          {formData.codelistA?.label && formData.codelistB?.label ? (
            <ReviewLineItem step={1} title="Report request">
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
            <ReviewLineItem step={1} title="Report request">
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

          <ReviewLineItem step={3} title="Filter population">
            {
              filterPopulation.items.filter(
                (item) => item.value === formData.filterPopulation
              )[0].label
            }
          </ReviewLineItem>

          <ReviewLineItem
            step={3}
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

export default Step5;
