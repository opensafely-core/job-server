import { useFormikContext } from "formik";
import { useFormStore } from "../../stores/form";
import Button from "./Button";

function CodelistButton({
  secondCodelist,
  setSecondCodelist,
}: {
  secondCodelist: boolean;
  setSecondCodelist: Function;
}) {
  const { setFieldValue, setTouched, validateForm } = useFormikContext();

  const handleCodelistBtn = (show: boolean) => {
    if (!show) {
      setFieldValue("codelist1", undefined);
      setTouched("codelist1", false);
      useFormStore.setState({ formData: {} });
    }
    setSecondCodelist(show);
    setTimeout(() => validateForm(), 0);
  };

  return (
    <Button
      onClick={() => handleCodelistBtn(!secondCodelist)}
      size="sm"
      variant={secondCodelist ? "danger" : "primary"}
    >
      {secondCodelist ? "Remove second codelist" : "Add second codelist"}
    </Button>
  );
}

export default CodelistButton;
