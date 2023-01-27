import { Tab } from "@headlessui/react";
import { useFormikContext } from "formik";
import { useState } from "react";
import { useFormStore, usePageData } from "../stores";
import { FormDataTypes, FormSingleCodelist, PageCodelistGroup } from "../types";
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
  const pageData = usePageData((state) => state.pageData);
  const [query, setQuery] = useState("");
  const codelistID = `codelist${id}`;

  return (
    <Tab.Group
      as="div"
      className="mb-8"
      defaultIndex={pageData.findIndex(
        (type: PageCodelistGroup) =>
          type.id ===
          (formData?.[codelistID as keyof FormDataTypes] as FormSingleCodelist)
            ?.type
      )}
      onChange={() => {
        setQuery("");
        setFieldValue(codelistID, {});
      }}
    >
      <h2 className="text-2xl font-bold tracking-tight mb-1">{label} type</h2>
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
