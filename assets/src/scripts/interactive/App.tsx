import { Wizard } from "react-use-wizard";
import { Step0, Step1, Step2, Step3, Step4, Step5 } from "./components/Steps";
import Wrapper from "./components/Wrapper";

function App() {
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
