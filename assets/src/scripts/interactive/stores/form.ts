import { create } from "zustand";
import { CodelistType } from "../data/codelists";

export const useFormStore = create(() => ({
  formData: {},
}));

export interface FormDataCodelistTypes extends CodelistType {
  type: string;
}

export interface FormDataTypes {
  codelist0?: FormDataCodelistTypes;
  codelist1?: FormDataCodelistTypes;
  frequency?: string;
  codelistA?: FormDataCodelistTypes;
  codelistB?: FormDataCodelistTypes;
  timeValue?: number;
  timeScale?: string;
  timeEvent?: string;
  filterPopulation?: string;
  demographics?: string[];
}
