import { Combobox, Tab } from "@headlessui/react";
import {
  Field,
  FieldProps,
  FormikErrors,
  FormikTouched,
  useFormikContext,
} from "formik";
import {
  FormDataTypes,
  OpenCodelistSingleCodelist,
  PageCodelistGroup,
} from "../../types";
import { classNames } from "../../utils";
import ComboboxItem from "../ComboboxItem";
import InputError from "../InputError";

function TabPanel({
  codelistGroup,
  codelistID,
  query,
  setQuery,
}: {
  codelistGroup: PageCodelistGroup;
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
    errors: FormikErrors<FormDataTypes>;
    setFieldValue: (
      field: string,
      value: any,
      shouldValidate?: boolean
    ) => void;
    setTouched: (
      touched: FormikTouched<FormDataTypes>,
      shouldValidate?: boolean
    ) => void;
    touched: FormikTouched<FormDataTypes>;
  } = useFormikContext();

  return (
    <Tab.Panel key={codelistGroup.id}>
      <Field name={codelistID}>
        {({ field }: FieldProps) => (
          <div className="mt-2">
            <Combobox
              defaultValue={field.value}
              name={field.name}
              onChange={(e) => {
                setTouched({ ...touched, [codelistID]: true });
                setFieldValue(field.name, {
                  label: e.name,
                  organisation: e.organisation,
                  value: e.slug,
                  type: codelistGroup.id,
                });
              }}
            >
              <div className="relative w-full max-w-prose">
                <Combobox.Input
                  className={classNames(
                    "block w-full pl-3 pr-10 py-2 border-2 border-gray-400 rounded-md shadow-sm placeholder-gray-400",
                    "focus:cursor-text focus:outline-none focus:ring-oxford-500 focus:border-oxford-500"
                  )}
                  displayValue={(codelist: OpenCodelistSingleCodelist) =>
                    codelist.name
                  }
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Type 3 or more characters to find a codelist"
                />
                <Combobox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base divide-y divide-gray-200 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <ComboboxItem codelistGroup={codelistGroup} query={query} />
                </Combobox.Options>
              </div>
            </Combobox>
            {errors?.[codelistID as keyof FormDataTypes] &&
            touched?.[codelistID as keyof FormDataTypes] ? (
              <InputError>Select a codelist</InputError>
            ) : null}
          </div>
        )}
      </Field>
    </Tab.Panel>
  );
}

export default TabPanel;
