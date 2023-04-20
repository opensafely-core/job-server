/* eslint-disable import/prefer-default-export */

export const queryText = [
  "The number of people who had",
  "added to their health record each month from",
  "to",
  "who have also had",
  "added to their health record in the same month as",
  "or",
];

export const timeQuery = "before.";

export const anyTimeQuery = "at any time prior.";

export const timeStatement = (values) =>
  `up to ${values.timeValue} ${values.timeScale} before.`;
