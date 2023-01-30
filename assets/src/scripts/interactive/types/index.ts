export interface OpenCodelist {
  name: string;
  organisation: string;
  slug: string;
}

export interface SingleCodelist {
  label: string;
  organisation: string;
  type: string;
  value: string;
}

export interface CodelistGroup {
  name: string;
  id: string;
  codelists: SingleCodelist[];
}

export interface FormDataTypes {
  codelist0?: SingleCodelist;
  codelist1?: SingleCodelist;
  frequency?: string;
  codelistA?: SingleCodelist;
  codelistB?: SingleCodelist;
  timeValue?: number;
  timeScale?: string;
  timeEvent?: string;
  filterPopulation?: string;
  demographics?: string[];
}
