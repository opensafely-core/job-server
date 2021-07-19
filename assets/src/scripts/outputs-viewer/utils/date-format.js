import { parse, format as fmt, isValid } from "date-fns";

export default function dateFmt({
  date,
  input = null,
  output = "d MMM yyyy 'at' HH:mm",
}) {
  let fileDate = new Date(date);

  if (!isValid(fileDate) || input) {
    fileDate = parse(date, input, new Date());
  }

  return fmt(fileDate, output);
}
