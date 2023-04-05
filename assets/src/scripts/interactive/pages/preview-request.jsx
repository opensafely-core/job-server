import { Redirect, useLocation } from "wouter";
import { AlertPage } from "../components/Alert";
import Button from "../components/Button";
import EventsBefore from "../components/Diagrams/EventsBefore";
import { useFormData } from "../context";
import { useRequiredFields } from "../utils";

function PreviewRequest() {
  const [, navigate] = useLocation();
  const { formData } = useFormData();

  if (useRequiredFields(["codelistA", "codelistB", "timeScale", "timeValue"])) {
    return <Redirect to="" />;
  }

  return (
    <>
      <AlertPage />
      <h1 className="text-4xl font-bold mb-8">Preview your request</h1>

      <div className="max-w-lg relative py-12">
        <p className="absolute max-w-[28ch] text-center top-0 right-0 border-2 border-oxford-300 bg-slate-50 p-2">
          Individual has qualifying event from:
          <br />
          <strong>{formData.codelistA.label}</strong>
        </p>

        <div className="pt-12 pb-6">
          <EventsBefore
            timeScale={formData.timeScale}
            timeValue={formData.timeValue}
          />
        </div>
        <p className="absolute max-w-[28ch] text-center bottom-0 left-0 border-2 border-oxford-300 bg-slate-50 p-2">
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
