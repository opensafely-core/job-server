import { Combobox } from "@headlessui/react";
import { CheckIcon } from "@heroicons/react/20/solid";
import { CodelistGroup, SingleCodelist } from "../types";
import { classNames } from "../utils";

function ComboboxItem({
  query,
  codelistGroup,
}: {
  query: string;
  codelistGroup: CodelistGroup;
}) {
  const filteredCodelists = (codelists: SingleCodelist[]) =>
    query.length < 2
      ? codelists
      : codelists.filter((codelist) =>
          codelist.label.toLowerCase().includes(query.toLowerCase())
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
        codelistGroup.codelists.sort((a, b) => a.label.localeCompare(b.label))
      ).map((codelist) => (
        <Combobox.Option
          key={codelist.value}
          className={({ active }) =>
            classNames(
              "relative cursor-pointer select-none py-2 pl-10 pr-4",
              active ? "bg-oxford-600 text-white" : "text-gray-900"
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
                    active ? "text-white" : "text-oxford-600"
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
