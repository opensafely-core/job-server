import { useFormikContext } from "formik";
import { bool, func } from "prop-types";
import { useFormStore } from "../../stores";
import Button from "./Button";

function CodelistButton({ secondCodelist, setSecondCodelist }) {
  const { setFieldValue, setTouched, touched, validateForm } =
    useFormikContext();

  const handleCodelistBtn = (show) => {
    if (!show) {
      setFieldValue("codelist1", undefined);
      setTouched({ ...touched, codelist1: false });
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

CodelistButton.propTypes = {
  secondCodelist: bool.isRequired,
  setSecondCodelist: func.isRequired,
};
