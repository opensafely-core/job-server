import { Tab } from "@headlessui/react";
import { useAppData } from "../../context";
import { classNames } from "../../utils";

function TabList() {
  const { codelistGroups } = useAppData();

  return (
    <Tab.List className="flex space-x-1 rounded bg-gray-100 p-1 max-w-prose">
      {codelistGroups.map((codelistGroup) => (
        <Tab
          key={codelistGroup.id}
          className={({ selected }) =>
            classNames(
              "w-full rounded-lg p-1 font-semibold text-oxford-700 leading-5 md:py-2.5",
              "ring-white ring-opacity-60 ring-offset-2 ring-offset-oxford-400 focus:outline-none focus:ring-2",
              selected
                ? "bg-white shadow"
                : "hover:bg-white/[0.12] hover:text-oxford-900",
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
