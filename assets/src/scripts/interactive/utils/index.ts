import { redirect } from "react-router-dom";
import { useFormStore } from "../stores";
import { OpenCodelist } from "../types";

export function classNames(...classes: (string | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function delay(ms: number) {
  // eslint-disable-next-line no-promise-executor-return
  return new Promise((res) => setTimeout(res, ms));
}

export function getCodelistPageData(scriptID: string) {
  const scriptTag = document.getElementById(scriptID);
  if (!scriptTag?.textContent) return [];

  const getJson: OpenCodelist[] = JSON.parse(scriptTag?.textContent);

  const configureJson = getJson.map((codelist) => ({
    label: codelist.name,
    organisation: codelist.organisation,
    type: scriptID,
    value: codelist.slug,
  }));

  return configureJson;
}

export function requiredLoader({ fields }: { fields: string[] }) {
  const { formData } = useFormStore.getState();
  const missing = [];

  fields.forEach((field) => {
    if (!Object.prototype.hasOwnProperty.call(formData, field)) {
      missing.push(field);
    }
  });

  if (missing.length) {
    return redirect("/");
  }

  return null;
}
