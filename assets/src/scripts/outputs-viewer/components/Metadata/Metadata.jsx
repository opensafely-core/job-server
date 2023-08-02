import React from "react";
import prettyFileSize from "../../utils/pretty-file-size";
import { selectedFileProps } from "../../utils/props";
import Link from "../Link";

function Metadata({ fileDate, fileName, fileSize, fileUrl }) {
  const fileDateValue = () => {
    if (Date.parse(fileDate)) {
      const getDate = new Date(fileDate);

      return {
        absolute: getDate.toISOString(),
        formatted: new Intl.DateTimeFormat("en-GB", {
          timeZone: "UTC",
          dateStyle: "short",
          timeStyle: "short",
        }).format(getDate),
      };
    }
    return false;
  };

  return (
    <ul className="flex flex-row gap-2 items-center w-full flex-wrap">
      <li className="mr-auto pr-4">
        <Link
          className={`
            font-semibold text-oxford-600 underline underline-offset-2 decoration-oxford-300 transition-colors duration-200
            hover:decoration-transparent hover:text-oxford
            focus:decoration-transparent focus:text-oxford focus:bg-bn-sun-300
            after:content-['↗'] after:text-sm after:ml-1 after:absolute after:mt-0.5
          `}
          href={fileUrl}
          newTab
        >
          {fileName}
        </Link>
      </li>
      {fileDateValue() && (
        <li className="font-mono text-sm text-right whitespace-nowrap">
          <div className="sr-only">Last modified at: </div>
          <time
            className=""
            dateTime={fileDateValue().absolute}
            title={fileDateValue().absolute}
          >
            {fileDateValue().formatted}
          </time>
        </li>
      )}
      <li className="font-mono text-sm text-right whitespace-nowrap ml-4">
        {prettyFileSize(fileSize)}
      </li>
    </ul>
  );
}

export default Metadata;

Metadata.propTypes = {
  fileDate: selectedFileProps.date.isRequired,
  fileName: selectedFileProps.name.isRequired,
  fileSize: selectedFileProps.size.isRequired,
  fileUrl: selectedFileProps.url.isRequired,
};
