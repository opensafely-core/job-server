import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import EventsAfter from "../components/Diagrams/EventsAfter";
import EventsBefore from "../components/Diagrams/EventsBefore";
import { useFormStore } from "../stores";
import { FormDataTypes } from "../types";
import { requiredLoader } from "../utils";

export const PreviewRequestLoader = () =>
  requiredLoader({
    fields: ["codelistA", "codelistB"],
  });

function PreviewRequest() {
  const navigate = useNavigate();
  const formData: FormDataTypes = useFormStore((state) => state.formData);

  const validData =
    formData.codelistA?.label &&
    formData.codelistB?.label &&
    formData.timeScale &&
    formData.timeValue;

  const isEventsBefore = () => {
    if (validData && formData.timeEvent === "before") {
      return true;
    }
    return false;
  };

  const isEventsAfter = () => {
    if (validData && formData.timeEvent === "after") {
      return true;
    }
    return false;
  };

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

      {isEventsAfter() ? (
        <div className="max-w-lg relative py-12">
          <p className="absolute max-w-[28ch] text-center left-0 top-0 border-2 border-oxford-300 bg-slate-50 p-2">
            Individual has qualifying event from:
            <br />
            <strong>{formData.codelistA!.label}</strong>
          </p>
          <EventsAfter
            timeScale={formData.timeScale}
            timeValue={formData.timeValue}
          />
          <p className="absolute max-w-[28ch] text-center right-0 bottom-0 border-2 border-oxford-300 bg-slate-50 p-2">
            Individual ALSO has an event from:
            <br />
            <strong>{formData.codelistB!.label}</strong>
          </p>
        </div>
      ) : null}

      <div className="flex flex-row w-full gap-2 mt-10">
        <Button onClick={() => navigate("/filter-request")}>Next</Button>
      </div>
    </>
  );
}

export default PreviewRequest;
