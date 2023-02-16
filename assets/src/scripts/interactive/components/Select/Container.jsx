import { Listbox, Transition } from "@headlessui/react";
import { ChevronUpDownIcon } from "@heroicons/react/20/solid";
import { func, shape, string } from "prop-types";
import { Fragment } from "react";
import { useFormData } from "../../context";
import { singleCodelistProps } from "../../props";
import { classNames } from "../../utils";
import SelectOption from "./Option";

function SelectContainer({ defaultValue, handleChange, name }) {
  const { formData } = useFormData();

  return (
    <Listbox
      name={name}
      onChange={(selected) => handleChange(selected)}
      value={defaultValue}
    >
      <div className="relative mt-1">
        <Listbox.Button
          className={classNames(
            "relative w-fit max-w-prose rounded-md border-gray-400 border-2 bg-white py-2 pl-3 pr-10 text-left shadow-sm",
            "focus:outline-none",
            "focus-visible:border-oxford-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300"
          )}
        >
          {({ value }) => (
            <>
              <span className="block truncate">{value.label}</span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 ">
                <ChevronUpDownIcon
                  aria-hidden="true"
                  className="h-5 w-5 text-gray-400"
                />
              </span>
            </>
          )}
        </Listbox.Button>
        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-fit max-w-prose overflow-auto rounded-md bg-white py-1 text-base divide-y divide-gray-200 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
            {formData.codelist0 ? (
              <SelectOption
                label={formData.codelist0.label}
                value={formData.codelist0}
              />
            ) : null}
            {formData.codelist1 ? (
              <SelectOption
                label={formData.codelist1.label}
                value={formData.codelist1}
              />
            ) : null}
          </Listbox.Options>
        </Transition>
      </div>
    </Listbox>
  );
}

export default SelectContainer;

SelectContainer.propTypes = {
  defaultValue: shape(singleCodelistProps).isRequired,
  handleChange: func.isRequired,
  name: string.isRequired,
};
