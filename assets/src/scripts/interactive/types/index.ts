export interface OpenCodelistSingleCodelist {
  name: string;
  organisation: string;
  slug: string;
}

export interface PageCodelistGroup {
  name: string;
  id: string;
  codelists: OpenCodelistSingleCodelist[];
}

export interface FormSingleCodelist {
  label: string;
  organisation: string;
  value: string;
  type: string;
}

export interface FormDataTypes {
  codelist0?: FormSingleCodelist;
  codelist1?: FormSingleCodelist;
  frequency?: string;
  codelistA?: FormSingleCodelist;
  codelistB?: FormSingleCodelist;
  timeValue?: number;
  timeScale?: string;
  timeEvent?: string;
  filterPopulation?: string;
  demographics?: string[];
}
