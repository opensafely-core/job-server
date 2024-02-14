import { Link, Redirect } from "wouter";
import { AlertPage } from "../components/Alert";
import Button from "../components/Button";
import EventsBefore from "../components/Diagrams/EventsBefore";
import { useFormData } from "../context";
import { useRequiredFields } from "../utils";

function PreviewRequest() {
  const { formData } = useFormData();

  if (useRequiredFields(["codelistA", "codelistB", "timeOption"])) {
    return <Redirect to="" />;
  }

  return (
    <>
      <AlertPage />
      <h1 className="text-4xl font-bold mb-8">Preview your request</h1>

      <div className="px-4 py-24">
        <div className="relative">
          <p className="absolute max-w-[28ch] text-center -translate-y-[80%] top-0 right-0 border-2 border-oxford-300 bg-slate-50 p-2">
            Individual has qualifying event from:
            <br />
            <strong>{formData.codelistA.label}</strong>
          </p>
          <EventsBefore
            timeOption={formData.timeOption}
            timeScale={formData.timeScale}
            timeValue={formData.timeValue}
          />
          <p className="absolute max-w-[28ch] text-center bottom-0 translate-y-[80%] left-0 border-2 border-oxford-300 bg-slate-50 p-2">
            Individual ALSO has an event from:
            <br />
            <strong>{formData.codelistB.label}</strong>
          </p>
        </div>
      </div>

      <div className="flex flex-row w-full gap-2 mt-16">
        <Link asChild to="/filter-request">
          <Button>Next</Button>
        </Link>
      </div>
    </>
  );
}

export default PreviewRequest;
