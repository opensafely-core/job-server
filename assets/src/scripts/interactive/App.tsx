import { Wizard } from "react-use-wizard";
import { Step0, Step1, Step2, Step3, Step4, Step5 } from "./components/Steps";
import Wrapper from "./components/Wrapper";
import { usePageData } from "./stores";
import { getCodelistPageData } from "./utils";

function App({ events, medications }: { events: string; medications: string }) {
  usePageData.setState({
    pageData: [
      {
        name: "Event",
        id: events,
        codelists: getCodelistPageData(events),
      },
      {
        name: "Medication",
        id: medications,
        codelists: getCodelistPageData(medications),
      },
    ],
  });

  return (
    <Wizard wrapper={<Wrapper />}>
      <Step0 />
      <Step1 />
      <Step2 />
      <Step3 />
      <Step4 />
      <Step5 />
    </Wizard>
  );
}

export default App;
