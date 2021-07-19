import { parse, format as fmt, isValid } from "date-fns";

export default function dateFmt({ date, format }) {
  let fileDate = new Date(date);

  if (!isValid(fileDate)) {
    fileDate = parse(date, format, new Date());
  }

  return fmt(fileDate, "d MMM yyyy 'at' HH:mm");
}
