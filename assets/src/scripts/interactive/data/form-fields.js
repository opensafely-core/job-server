export const dataDates = () => {
  const start = new Date(Date.UTC(2019, 8, 1));
  const end = new Date(Date.UTC(2022, 11, 7));

  const options = {
    year: "numeric",
    month: "long",
    day: "numeric",
  };

  return {
    endISO: end.toISOString(),
    endStr: end.toLocaleDateString("en-GB", options),
    startISO: start.toISOString(),
    startStr: start.toLocaleDateString("en-GB", options),
  };
};

export const frequency = {
  label: "How would you like to group events?",
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
