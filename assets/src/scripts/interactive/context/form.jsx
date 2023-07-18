import { element } from "prop-types";
import { createContext, useContext, useMemo, useState } from "react";

const FormData = createContext();
FormData.displayName = "FormData";

function FormDataProvider({ children }) {
  const [formData, setFormData] = useState({});
  const value = useMemo(() => ({ formData, setFormData }), [formData]);
  return <FormData.Provider value={value}>{children}</FormData.Provider>;
}

function useFormData() {
  const context = useContext(FormData);
  if (context === undefined) {
    throw new Error(
      "useFormData must be used within a FormData.Provider component",
    );
  }
  return context;
}

export { useFormData, FormDataProvider };

FormDataProvider.propTypes = {
  children: element.isRequired,
};
