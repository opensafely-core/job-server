import { Combobox, Tab } from "@headlessui/react";
import { ArrowUpRightIcon } from "@heroicons/react/20/solid";
import { Field, useFormikContext } from "formik";
import { func, shape, string } from "prop-types";
import { useEffect, useState } from "react";
import { codelistGroupProps } from "../../props";
import { classNames, isObject } from "../../utils";
import ComboboxItem from "../ComboboxItem";
import InputError from "../InputError";

function TabPanel({ codelistGroup, codelistID, query, setQuery }) {
  const { errors, setFieldValue, setTouched, touched } = useFormikContext();
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
        {({ field }) => (
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
                  autoComplete="off"
                  autoCorrect="false"
                  className={classNames(
                    "block w-full px-3 py-2 border-2 border-gray-400 rounded-md shadow-sm placeholder-gray-400",
                    "focus:cursor-text focus:outline-none focus:ring-oxford-500 focus:border-oxford-500"
                  )}
                  displayValue={(codelist) => codelist.label}
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
            {field?.value?.value ? (
              <ul className="text-sm mt-2">
                <li>
                  <a
                    className="text-oxford-600 font-semibold underline underline-offset-1 transition-colors hover:text-oxford-700 hover:no-underline focus:text-oxford-900 focus:no-underline"
                    href={`https://www.opencodelists.org/codelist/${field.value.value}`}
                    rel="noopener noreferrer"
                    target="_blank"
                  >
                    View “{field.value.label}” codelist
                    <ArrowUpRightIcon
                      className="inline h-4 -mt-0.5"
                      height={20}
                      width={20}
                    />
                  </a>
                </li>
              </ul>
            ) : null}
          </div>
        )}
      </Field>
    </Tab.Panel>
  );
}

export default TabPanel;

TabPanel.propTypes = {
  codelistGroup: shape(codelistGroupProps).isRequired,
  codelistID: string.isRequired,
  query: string.isRequired,
  setQuery: func.isRequired,
};
