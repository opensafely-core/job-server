import { useEffect } from "react";
import { Redirect } from "wouter";
import { removeAlert } from "../components/Alert";
import { useFormData } from "../context";
import { useRequiredFields } from "../utils";

function Success() {
  const uuid = crypto.randomUUID().split("-").slice(0, 1)[0];
  const { setFormData } = useFormData();

  if (
    useRequiredFields([
      "codelist0",
      "frequency",
      "filterPopulation",
      "demographics",
    ])
  ) {
    return <Redirect to="" />;
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    removeAlert();
    return setFormData({});
  }, [setFormData]);

  return (
    <div className="prose prose-lg mb-10">
      <h1>Your request is being processed</h1>
      <p>
        Your reference number:{` `}
        <span className="font-bold font-mono">{uuid}</span>
      </p>
      <p>We will notify you when your analysis is ready.</p>
      <p>
        The results will be checked carefully by our team for privacy and
        security reasons. We aim to process requests within two working days.
      </p>
    </div>
  );
}

export default Success;
