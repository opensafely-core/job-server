import { string } from "prop-types";

// export const OpenCodelist = {
//   name: string;
//   organisation: string;
//   slug: string;
// }

export const singleCodelistProps = {
  label: string,
  organisation: string,
  type: string,
  value: string,
};

export const codelistGroupProps = {
  name: string.isRequired,
  id: string.isRequired,
  codelists: singleCodelistProps,
};

// export const FormDataTypes = {
//   codelist0?: SingleCodelist;
//   codelist1?: SingleCodelist;
//   frequency?: string;
//   codelistA?: SingleCodelist;
//   codelistB?: SingleCodelist;
//   timeValue?: number;
//   timeScale?: string;
//   timeEvent?: string;
//   filterPopulation?: string;
//   demographics?: string[];
// }
