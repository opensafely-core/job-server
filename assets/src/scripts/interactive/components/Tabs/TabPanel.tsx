import { Combobox, Tab } from "@headlessui/react";
import { Field, FieldProps, FormikTouched, useFormikContext } from "formik";
import { useEffect, useState } from "react";
import { CodelistGroup, FormDataTypes, SingleCodelist } from "../../types";
import { classNames, isObject } from "../../utils";
import ComboboxItem from "../ComboboxItem";
import InputError from "../InputError";

function TabPanel({
  codelistGroup,
  codelistID,
  query,
  setQuery,
}: {
  codelistGroup: CodelistGroup;
  codelistID: string;
  query: string;
  setQuery: Function;
}) {
  const {
    errors,
    setFieldValue,
    setTouched,
    touched,
  }: {
    errors: { [index: string]: any };
    setFieldValue: (
      field: string,
      value: any,
      shouldValidate?: boolean
    ) => void;
    setTouched: (
      touched: FormikTouched<FormDataTypes>,
      shouldValidate?: boolean
    ) => void;
    touched: { [index: string]: any };
  } = useFormikContext();
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (errors[codelistID] && touched[codelistID]) {
      if (isObject(errors[codelistID])) {
        return setErrorMsg(errors[codelistID].label);
      }
      return setErrorMsg(errors[codelistID]);
    }

    return setErrorMsg("");
  }, [errors, touched, codelistID]);

  return (
    <Tab.Panel key={codelistGroup.id}>
      <Field name={codelistID}>
        {({ field }: FieldProps) => (
          <div className="mt-2">
            <Combobox
              defaultValue={field.value}
              name={field.name}
              onChange={(selectedItem) => {
                setTouched({ ...touched, [codelistID]: true });
                setFieldValue(field.name, selectedItem);
              }}
            >
              <div className="relative w-full max-w-prose">
                <Combobox.Input
                  className={classNames(
                    "block w-full px-3 py-2 border-2 border-gray-400 rounded-md shadow-sm placeholder-gray-400",
                    "focus:cursor-text focus:outline-none focus:ring-oxford-500 focus:border-oxford-500"
                  )}
                  displayValue={(codelist: SingleCodelist) => codelist.label}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Type 3 or more characters to find a codelist"
                />
                <Combobox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base divide-y divide-gray-200 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <ComboboxItem
                    codelistGroup={codelistGroup}
                    codelistID={codelistID}
                    query={query}
                  />
                </Combobox.Options>
              </div>
            </Combobox>
            {errorMsg ? <InputError>{errorMsg}</InputError> : null}
          </div>
        )}
      </Field>
    </Tab.Panel>
  );
}

export default TabPanel;
