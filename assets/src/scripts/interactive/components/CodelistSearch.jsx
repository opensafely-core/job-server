import { Tab } from "@headlessui/react";
import { useFormikContext } from "formik";
import { number, string } from "prop-types";
import { useState } from "react";
import { useAppData, useFormData } from "../context";
import { TabList, TabPanel } from "./Tabs";

function CodelistSearch({ id, label }) {
  const { setFieldValue } = useFormikContext();
  const { formData } = useFormData();
  const { codelistGroups } = useAppData();
  const [query, setQuery] = useState("");
  const codelistID = `codelist${id}`;
  const defaultIndex = codelistGroups.findIndex(
    (group) => group.id === formData?.[codelistID]?.type,
  );

  return (
    <Tab.Group
      as="div"
      defaultIndex={defaultIndex !== -1 ? defaultIndex : 0}
      onChange={() => {
        setQuery("");
        setFieldValue(codelistID, {});
      }}
    >
      <h2 className="text-2xl font-bold tracking-tight mb-2 md:mb-1">
        {label}
      </h2>
      <TabList />
      <Tab.Panels>
        {codelistGroups.map((codelistGroup) => (
          <TabPanel
            key={codelistGroup.id}
            codelistGroup={codelistGroup}
            codelistID={codelistID}
            query={query}
            setQuery={setQuery}
          />
        ))}
      </Tab.Panels>
    </Tab.Group>
  );
}

export default CodelistSearch;

CodelistSearch.propTypes = {
  id: number.isRequired,
  label: string.isRequired,
};
