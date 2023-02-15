import { useFormStore } from "../stores";

export function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function delay(ms) {
  // eslint-disable-next-line no-promise-executor-return
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
    value: codelist.slug,
  }));

  return configureJson;
}

export function requiredLoader({ fields }) {
  const { formData } = useFormStore.getState();
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
