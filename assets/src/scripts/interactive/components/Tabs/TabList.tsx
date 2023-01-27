import { Tab } from "@headlessui/react";
import { usePageData } from "../../stores";
import { classNames } from "../../utils";

function TabList() {
  const pageData = usePageData((state) => state.pageData);

  return (
    <Tab.List className="flex space-x-1 rounded bg-gray-100 p-1 max-w-prose">
      {pageData.map((codelistGroup) => (
        <Tab
          key={codelistGroup.id}
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
          {codelistGroup.name}
        </Tab>
      ))}
    </Tab.List>
  );
}

export default TabList;
