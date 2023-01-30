import { array, lazy, number, object, string, TestContext } from "yup";
import {
  builderTimeEvents,
  builderTimeScales,
  demographics,
  filterPopulation,
} from "./form-fields";

const codelist = object()
  .shape({
    label: string().required("Select a codelist"),
    organisation: string(),
    value: string().required("Select a codelist"),
    type: string()
      // .oneOf(codelistData.map((type) => type.id))
      .required(),
  })
  .required("Select a codelist");

export const step0Schema = (secondCodelist: Boolean) =>
  lazy(() =>
    object({
      codelist0: codelist,
      codelist1: secondCodelist
        ? codelist.test(
            "compare_codelists",
            "Codelists cannot be the same, please change one codelist",
            (value: string, testContext: TestContext) => {
              if (
                Object.entries(testContext.parent.codelist0).toString() ===
                Object.entries(value).toString()
              ) {
                return false;
              }

              return true;
            }
          )
        : undefined,
      frequency: string()
        .oneOf(["monthly", "quarterly", "yearly"])
        .required("Select a frequency"),
    })
  );

export const step1Schema = object().shape({
  codelistA: codelist,
  codelistB: codelist,
  timeValue: number().required(),
  timeScale: string()
    .oneOf(builderTimeScales.map((event) => event.value))
    .required(),
  timeEvent: string()
    .oneOf(builderTimeEvents.map((event) => event.value))
    .required(),
});

export const step3Schema = object().shape({
  filterPopulation: string()
    .oneOf(filterPopulation.items.map((item) => item.value))
    .required("Select a filter for the population"),
  demographics: array()
    .of(string().oneOf(demographics.items.map((item) => item.value)))
    .min(1)
    .max(demographics.items.length)
    .required(),
});
