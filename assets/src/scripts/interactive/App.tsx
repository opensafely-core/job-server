import { Outlet } from "react-router-dom";
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
    <Wrapper>
      <Outlet />
    </Wrapper>
  );
}

export default App;
