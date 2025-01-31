import { useFormData } from "../context";
import { dataDates } from "../data/form-fields";

export function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function delay(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

export function getCodelistPageData(scriptID) {
  const scriptTag = document.getElementById(scriptID);
  if (!scriptTag?.textContent) return [];

  const getJson = JSON.parse(scriptTag?.textContent);

  const configureJson = getJson.map((codelist) => ({
    label: codelist.name,
    organisation: codelist.organisation,
    type: scriptID.slice(9, scriptID.length - 1),
    user: codelist.user,
    value: codelist.slug,
    updatedDate: codelist.updated_date,
  }));

  return configureJson;
}

export function useRequiredFields(fields) {
  const { formData } = useFormData();
  const missing = [];

  fields.forEach((field) => {
    if (!Object.prototype.hasOwnProperty.call(formData, field)) {
      missing.push(field);
    }
  });

  return !!missing.length;
}

export function isObject(a) {
  return !!a && a.constructor === Object;
}

export function getAppData({
  dataset: { basePath, csrfToken, events, medications, dateStart, dateEnd },
}) {
  return {
    basePath,
    csrfToken,
    codelistGroups: [
      {
        name: "SNOMED CT",
        id: "event",
        codelists: getCodelistPageData(events),
      },
      {
        name: "dm+d",
        id: "medication",
        codelists: getCodelistPageData(medications),
      },
    ],
    dates: { ...dataDates({ dateStart, dateEnd }) },
  };
}

export const removeUndefinedValuesFromObject = (obj) => {
  Object.keys(obj).forEach((key) => obj[key] === undefined && delete obj[key]);
  return obj;
};
