export const endDate = "7th December 2022";

export const frequency = {
  label: "Select a frequency to group events by",
  items: [
    { label: "Monthly", value: "monthly" },
    { label: "Quarterly", value: "quarterly" },
    { label: "Yearly", value: "yearly" },
  ],
};

export const builderTimeScales = [
  { label: "Weeks", value: "weeks" },
  { label: "Months", value: "months" },
  { label: "Years", value: "years" },
];

export const builderTimeEvents = [
  {
    label: "Before",
    value: "before",
  },
  {
    label: "After",
    value: "after",
  },
];

export const filterPopulation = {
  label: "Filter the population",
  items: [
    { label: "All people", value: "all" },
    { label: "Adults only", value: "adults" },
    { label: "Children only", value: "children" },
  ],
};

export const demographics = {
  label: "Break down the report by demographics",
  items: [
    { label: "Sex", value: "sex" },
    { label: "Age", value: "age" },
    { label: "Ethnicity", value: "ethnicity" },
    { label: "Index of Multiple Deprivation (IMD)", value: "imd" },
    { label: "Region", value: "region" },
  ],
};
