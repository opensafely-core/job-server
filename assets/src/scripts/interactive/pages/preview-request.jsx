import { Redirect, useLocation } from "wouter";
import { AlertPage } from "../components/Alert";
import { Button } from "../components/Button";
import EventsAfter from "../components/Diagrams/EventsAfter";
import EventsBefore from "../components/Diagrams/EventsBefore";
import { useFormData } from "../context";
import { useRequiredFields } from "../utils";

function PreviewRequest() {
  const [, navigate] = useLocation();
  const { formData } = useFormData();

  if (useRequiredFields(["codelistA", "codelistB"])) {
    return <Redirect to="" />;
  }

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
      <AlertPage />
      <h1 className="text-4xl font-bold mb-8">Preview your request</h1>

      <div className="max-w-lg relative py-12">
        <p className="absolute max-w-[28ch] text-center left-0 top-0 border-2 border-oxford-300 bg-slate-50 p-2">
          Individual has qualifying event from:
          <br />
          <strong>{formData.codelistA.label}</strong>
        </p>
        {isEventsBefore() ? (
          <EventsBefore
            timeScale={formData.timeScale}
            timeValue={formData.timeValue}
          />
        ) : null}
        {isEventsAfter() ? (
          <EventsAfter
            timeScale={formData.timeScale}
            timeValue={formData.timeValue}
          />
        ) : null}
        <p className="absolute max-w-[28ch] text-center right-0 bottom-0 border-2 border-oxford-300 bg-slate-50 p-2">
          Individual ALSO has an event from:
          <br />
          <strong>{formData.codelistB.label}</strong>
        </p>
      </div>

      <div className="flex flex-row w-full gap-2 mt-10">
        <Button onClick={() => navigate("filter-request")}>Next</Button>
      </div>
    </>
  );
}

export default PreviewRequest;
