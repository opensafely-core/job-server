import { arrayOf, shape, string } from "prop-types";

export const singleCodelistProps = {
  label: string,
  organisation: string,
  type: string,
  user: string,
  value: string,
};

export const codelistGroupProps = {
  name: string.isRequired,
  id: string.isRequired,
  codelists: arrayOf(shape(singleCodelistProps)).isRequired,
};
