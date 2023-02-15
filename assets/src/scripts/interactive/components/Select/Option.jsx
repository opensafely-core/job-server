import { Listbox } from "@headlessui/react";
import { CheckIcon } from "@heroicons/react/20/solid";
import { string } from "prop-types";
import { singleCodelistProps } from "../../props";
import { classNames } from "../../utils";

function SelectOption({ label, value }) {
  return (
    <Listbox.Option
      className={({ active }) =>
        classNames(
          "relative cursor-pointer select-none py-2 pl-10 pr-4",
          active ? "bg-oxford-600 text-white" : "text-gray-900"
        )
      }
      value={value}
    >
      {({ selected, active }) => (
        <>
          <span
            className={classNames(
              "block truncate",
              selected ? "font-medium" : "font-normal"
            )}
          >
            <span>{label}</span>
          </span>
          {selected ? (
            <span
              className={classNames(
                "absolute inset-y-0 left-0 flex items-center px-3 z-10",
                active ? "text-white" : "text-oxford-600"
              )}
            >
              <CheckIcon aria-hidden="true" className="h-5 w-5" />
            </span>
          ) : null}
        </>
      )}
    </Listbox.Option>
  );
}

export default SelectOption;

SelectOption.propTypes = {
  label: string.isRequired,
  value: singleCodelistProps.isRequired,
};
