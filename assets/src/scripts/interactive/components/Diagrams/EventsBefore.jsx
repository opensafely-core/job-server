import { number, string } from "prop-types";

function EventsBefore({ timeScale, timeValue }) {
  return (
    <svg viewBox="-0.5 -0.5 372 301" xmlns="http://www.w3.org/2000/svg">
      <path
        className="stroke-gray-300 fill-none stroke-[3]"
        d="M160 70v120M320 70v120"
      />
      <text
        className="font-sans text-xs text-gray-800"
        textAnchor="middle"
        x="160"
        y="205"
      >
        Start of month
      </text>
      <text
        className="font-sans text-xs text-gray-800"
        textAnchor="middle"
        x="320"
        y="205"
      >
        End of month
      </text>
      <path
        className="stroke-green-600 fill-none stroke-[3]"
        d="M50.1 150h199.8"
      />
      <path
        className="fill-green-600 stroke-green-600 stroke-[3]"
        d="m43.4 150 9-4.5L50 150l2.3 4.5Zm213.3 0-9 4.5 2.2-4.5-2.3-4.5Z"
      />
      <path
        className="stroke-oxford-300 fill-none stroke-[3]"
        d="m80 270 18.2-100"
      />
      <path
        className="fill-oxford-300 stroke-oxford-300 stroke-[3]"
        d="m99.4 163.3 2.8 9.7-4-3-4.8 1.3Z"
      />
      <text
        className="fill-green-600 font-sans text-xs"
        textAnchor="middle"
        x="100"
        y="140"
      >
        {timeValue} {timeScale}
      </text>
      <path
        className="fill-none stroke-oxford-300 stroke-[3]"
        d="m280 30-9 90"
      />
      <path
        className="fill-oxford-300 stroke-oxford-300 stroke-[3]"
        d="m270.3 126.7-3.6-9.4 4.3 2.6 4.7-1.7Z"
      />
      <path
        className="stroke-bn-ribbon-600 fill-bn-ribbon-200"
        d="M258 140h5.8l4.2 6 4.2-6h5.8l-7 10 7 10h-5.8l-4.2-6-4.2 6H258l6.7-10Z"
      />
    </svg>
  );
}

export default EventsBefore;

EventsBefore.propTypes = {
  timeScale: string.isRequired,
  timeValue: number.isRequired,
};
