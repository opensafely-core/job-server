import { Combobox, Tab } from "@headlessui/react";
import { CheckIcon, ChevronUpDownIcon } from "@heroicons/react/20/solid";
import {
  Field,
  FieldProps,
  FormikErrors,
  FormikTouched,
  useFormikContext,
} from "formik";
import { useState } from "react";
import { codelistData, CodelistPageDataTypes } from "../data/codelists";
import {
  FormDataCodelistTypes,
  FormDataTypes,
  useFormStore,
} from "../stores/form";
import { classNames } from "../utils";
import InputError from "./InputError";

function CodelistSearch({ id, label }: { id: number; label: string }) {
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
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const [query, setQuery] = useState("");
  const codelistID = `codelist${id}`;

  const filteredCodelists = (
    codelists: { label: string; value: string; organisation: string }[]
  ) =>
    query === ""
      ? codelists
      : codelists.filter((codelist) =>
          codelist.label.toLowerCase().includes(query.toLowerCase())
        );

  return (
    <Tab.Group
      as="div"
      className="mb-8"
      defaultIndex={codelistData.findIndex(
        (type: CodelistPageDataTypes) =>
          type.id ===
          (
            formData?.[
              codelistID as keyof FormDataTypes
            ] as FormDataCodelistTypes
          )?.type
      )}
      onChange={() => {
        setQuery("");
        setFieldValue(codelistID, {});
      }}
    >
      <h2 className="text-2xl font-bold tracking-tight mb-1">{label} type</h2>
      <Tab.List className="flex space-x-1 rounded bg-gray-100 p-1 max-w-prose">
        {codelistData.map((codelistType) => (
          <Tab
            key={codelistType.id}
            className={({ selected }) =>
              classNames(
                "w-full rounded-lg py-2.5 font-semibold text-oxford-700 leading-5",
                "ring-white ring-opacity-60 ring-offset-2 ring-offset-oxford-400 focus:outline-none focus:ring-2",
                selected
                  ? "bg-white shadow"
                  : "hover:bg-white/[0.12] hover:text-oxford-900"
              )
            }
          >
            {codelistType.name}
          </Tab>
        ))}
      </Tab.List>
      <Tab.Panels>
        {codelistData.map((codelistType) => (
          <Tab.Panel key={codelistType.id}>
            <Field name={codelistID}>
              {({ field }: FieldProps) => (
                <div className="mt-2">
                  <Combobox
                    defaultValue={field.value}
                    name={field.name}
                    onChange={(e) => {
                      setTouched({ ...touched, [codelistID]: true });
                      setFieldValue(field.name, {
                        ...e,
                        type: codelistType.id,
                      });
                    }}
                  >
                    <div className="relative w-full max-w-prose">
                      <Combobox.Button as="div">
                        <Combobox.Input
                          className={classNames(
                            "block w-full pl-3 pr-10 py-2 border-2 border-gray-400 rounded-md shadow-sm placeholder-gray-400",
                            "focus:cursor-text focus:outline-none focus:ring-oxford-500 focus:border-oxford-500"
                          )}
                          displayValue={(codelist: FormDataCodelistTypes) =>
                            codelist.label
                          }
                          onChange={(event) => setQuery(event.target.value)}
                          placeholder={label}
                        />
                      </Combobox.Button>
                      <Combobox.Button className="absolute inset-y-0 right-0 flex items-center pr-2">
                        <ChevronUpDownIcon
                          aria-hidden="true"
                          className="h-5 w-5 text-gray-400"
                        />
                      </Combobox.Button>
                      <Combobox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base divide-y divide-gray-200 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                        {filteredCodelists(codelistType.codelists).length ===
                          0 && query !== "" ? (
                          <div className="relative cursor-default select-none py-2 px-4 text-gray-700">
                            Nothing found.
                          </div>
                        ) : (
                          filteredCodelists(
                            codelistType.codelists.sort((a, b) =>
                              a.label.localeCompare(b.label)
                            )
                          ).map((codelist) => (
                            <Combobox.Option
                              key={codelist.value}
                              className={({ active }) =>
                                classNames(
                                  "relative cursor-pointer select-none py-2 pl-10 pr-4",
                                  active
                                    ? "bg-oxford-600 text-white"
                                    : "text-gray-900"
                                )
                              }
                              value={codelist}
                            >
                              {({ selected, active }) => (
                                <>
                                  <span
                                    className={classNames(
                                      "block truncate",
                                      selected ? "font-medium" : "font-normal"
                                    )}
                                  >
                                    <span>{codelist.label}</span>
                                    <span
                                      className={`block text-sm ${
                                        active ? "text-white" : "text-gray-600"
                                      }`}
                                    >
                                      From: {codelist.organisation}
                                    </span>
                                  </span>
                                  {selected ? (
                                    <span
                                      className={classNames(
                                        "absolute inset-y-0 left-0 flex items-center pl-3 z-10",
                                        active
                                          ? "text-white"
                                          : "text-oxford-600"
                                      )}
                                    >
                                      <CheckIcon
                                        aria-hidden="true"
                                        className="h-5 w-5"
                                      />
                                    </span>
                                  ) : null}
                                </>
                              )}
                            </Combobox.Option>
                          ))
                        )}
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
        ))}
      </Tab.Panels>
    </Tab.Group>
  );
}

export default CodelistSearch;
