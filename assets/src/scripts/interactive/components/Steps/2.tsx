import { useWizard } from "react-use-wizard";
import { FormDataTypes, useFormStore } from "../../stores/form";
import { scrollToTop } from "../../utils";
import { Button } from "../Button";
import EventsBefore from "../Diagrams/EventsBefore";
import FormDebug from "../FormDebug";

function Step3() {
  const { handleStep, nextStep } = useWizard();
  const formData: FormDataTypes = useFormStore((state) => state.formData);

  const isEventsBefore = () => {
    if (
      formData.codelistA?.label &&
      formData.codelistB?.label &&
      formData.timeEvent === "before" &&
      formData.timeScale &&
      formData.timeValue
    ) {
      return true;
    }
    return false;
  };

  handleStep(() => scrollToTop());

  return (
    <>
      <h1 className="text-4xl font-bold mb-8">Preview your request</h1>

      {isEventsBefore() ? (
        <div className="max-w-lg relative py-12">
          <p className="absolute max-w-[28ch] text-center right-0 top-0 border-2 border-oxford-300 bg-slate-50 p-2">
            Individual has qualifying event from:
            <br />
            <strong>{formData.codelistA!.label}</strong>
          </p>
          <EventsBefore
            timeScale={formData.timeScale}
            timeValue={formData.timeValue}
          />
          <p className="absolute max-w-[28ch] text-center left-0 bottom-0 border-2 border-oxford-300 bg-slate-50 p-2">
            Individual ALSO has an event from:
            <br />
            <strong>{formData.codelistB!.label}</strong>
          </p>
        </div>
      ) : null}

      <div className="flex flex-row w-full gap-2 mt-10">
        <Button onClick={() => nextStep()}>Next</Button>
      </div>
      <FormDebug />
    </>
  );
}

export default Step3;
