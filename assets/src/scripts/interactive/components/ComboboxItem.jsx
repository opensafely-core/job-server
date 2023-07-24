import { Combobox } from "@headlessui/react";
import { CheckIcon } from "@heroicons/react/20/solid";
import { useFormikContext } from "formik";
import { shape, string } from "prop-types";
import { codelistGroupProps } from "../props";
import { classNames } from "../utils";

function dateFmt(date) {
  const options = {
    year: "numeric",
    month: "short",
    day: "2-digit",
  };
  const dateValue = new Date(date);
  const dateFormatted = new Intl.DateTimeFormat("en-GB", options).format(
    dateValue,
  );
  return dateFormatted;
}

function ComboboxItem({ codelistGroup, codelistID, query }) {
  const { values } = useFormikContext();
  const filteredCodelists = (codelists) =>
    query.length < 2
      ? codelists
      : codelists.filter((codelist) =>
          codelist.label.toLowerCase().includes(query.toLowerCase()),
        );

  if (query.length < 3) {
    return (
      <div className="relative cursor-default select-none py-2 px-4 text-gray-700">
        Type {3 - query.length} more characters to search
      </div>
    );
  }

  if (filteredCodelists(codelistGroup.codelists).length === 0) {
    return (
      <div className="relative cursor-default select-none py-2 px-4 text-gray-700">
        Nothing found
      </div>
    );
  }

  return (
    <>
      {filteredCodelists(
        codelistGroup.codelists.sort((a, b) => a.label.localeCompare(b.label)),
      ).map((codelist) => (
        <Combobox.Option
          key={codelist.value}
          className={({ active }) =>
            classNames(
              "relative cursor-pointer select-none py-2 pl-10 pr-4",
              active ? "bg-oxford-600 text-white" : "text-gray-900",
            )
          }
          value={codelist}
        >
          {({ selected, active }) => (
            <>
              <div
                className={classNames(
                  "block truncate",
                  selected ? "font-medium" : "font-normal",
                )}
              >
                <span>{codelist.label}</span>
                <dl
                  className={`flex flex-row flex-wrap text-sm mt-0.5 ${
                    active ? "text-white" : "text-gray-600"
                  }`}
                >
                  <div className="flex flex-row gap-1">
                    <dt>From:</dt>{" "}
                    <dd>
                      {codelist.organisation
                        ? codelist.organisation
                        : codelist.user}
                    </dd>
                  </div>
                  <div className="flex flex-row gap-1 ml-2 border-l border-l-gray-300 pl-2">
                    <dt>Last updated:</dt>{" "}
                    <dd>{dateFmt(codelist.updatedDate)}</dd>
                  </div>
                </dl>
              </div>
              {selected || values[codelistID]?.value === codelist.value ? (
                <span
                  className={classNames(
                    "absolute inset-y-0 left-0 flex items-center pl-3 z-10",
                    active ? "text-white" : "text-oxford-600",
                  )}
                >
                  <CheckIcon aria-hidden="true" className="h-5 w-5" />
                </span>
              ) : null}
            </>
          )}
        </Combobox.Option>
      ))}
    </>
  );
}

export default ComboboxItem;

ComboboxItem.propTypes = {
  codelistGroup: shape(codelistGroupProps).isRequired,
  codelistID: string.isRequired,
  query: string.isRequired,
};
