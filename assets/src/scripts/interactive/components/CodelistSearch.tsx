import { Tab } from "@headlessui/react";
import { useFormikContext } from "formik";
import { useState } from "react";
import { useFormStore, usePageData } from "../stores";
import { CodelistGroup, FormDataTypes, SingleCodelist } from "../types";
import TabList from "./Tabs/TabList";
import TabPanel from "./Tabs/TabPanel";

function CodelistSearch({ id, label }: { id: number; label: string }) {
  const {
    setFieldValue,
  }: {
    setFieldValue: (
      field: string,
      value: any,
      shouldValidate?: boolean
    ) => void;
  } = useFormikContext();
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const { pageData } = usePageData.getState();
  const [query, setQuery] = useState("");
  const codelistID = `codelist${id}`;
  const defaultIndex = pageData.findIndex(
    (group: CodelistGroup) =>
      group.id ===
      (formData?.[codelistID as keyof FormDataTypes] as SingleCodelist)?.type
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
        {pageData.map((codelistGroup) => (
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
