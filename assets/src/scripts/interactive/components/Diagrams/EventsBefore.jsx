import { number, string } from "prop-types";

function EventsBefore({ timeOption, timeScale, timeValue }) {
  const timeText =
    timeOption === "at any time prior."
      ? `any time`
      : `${timeValue} ${timeScale}`;

  return (
    <svg
      clipRule="evenodd"
      fillRule="evenodd"
      strokeLinejoin="round"
      strokeMiterlimit="2"
      viewBox="0 0 415 233"
      xmlns="http://www.w3.org/2000/svg"
      xmlSpace="preserve"
    >
      <path
        className="fill-gray-300"
        d="M194 52.03h6V157h-6zM394 52h6v105h-6z"
      />
      <path
        className="fill-gray-500"
        d="M3.9 99.9c-.6.5-.6 1.5 0 2l9.35 9.6c.26.2.57.3.89.3a1.5 1.5 0 0 0 1.18-2.4l-8.37-8.5 8.37-8.5a1.5 1.5 0 0 0-1.18-2.4c-.32 0-.63.1-.89.3l-9.46 9.5.1.1Zm189.1 2c.6-.5.6-1.5 0-2l-9.35-9.6c-.26-.2-.57-.3-.89-.3a1.5 1.5 0 0 0-1.18 2.4l8.37 8.5-8.37 8.5a1.5 1.5 0 0 0 1.18 2.4c.32 0 .63-.1.89-.3l9.46-9.5-.1-.1Zm-188.12.5h187.14v-3H4.88v3Z"
        fillRule="nonzero"
      />
      <path
        className="fill-green-600 stroke-green-600"
        d="M1 128c-.6.5-.6 1.5 0 2l9.5 9.6a1.5 1.5 0 0 0 2.1-2.1L4.1 129l8.5-8.5a1.5 1.5 0 0 0-2.1-2.1l-9.6 9.5.1.1Zm392 2c.6-.5.6-1.5 0-2l-9.5-9.6a1.5 1.5 0 0 0-2.1 2.1l8.5 8.5-8.5 8.5a1.5 1.5 0 0 0 2.1 2.1l9.6-9.5-.1-.1Zm-391 .5h390v-3H2v3Z"
        fillRule="nonzero"
        strokeWidth="2"
        transform="matrix(.99262 0 0 1 2.9 1.9)"
      />
      <path
        className="fill-bn-ribbon-300 stroke-bn-ribbon-700"
        d="M297 97.4 284.4 85l-3.5 3.5 12.5 12.5-12.4 12.3 3.5 3.5 12.4-12.4 12.4 12.4 3.5-3.5-12.4-12.4 12.4-12.4-3.5-3.5-12.4 12.4h.1Z"
      />
      <path
        className="fill-oxford-300"
        d="M296 74.55c.5.6 1.5.6 2 0l9.6-9.5a1.5 1.5 0 0 0-2.1-2.1l-8.5 8.5-8.5-8.5a1.5 1.5 0 0 0-2.1 2.1l9.5 9.6.1-.1Zm-.5-71v70h3v-70h-3ZM50 150.6c-.2-.8-1-1.3-1.8-1l-13 3.4a1.54 1.54 0 0 0 .7 3l11.6-3.2 3.1 11.6a1.5 1.5 0 0 0 2.9-.7l-3.5-13v-.1ZM3.3 232.4l46.6-80.6-2.6-1.6L.7 231l2.6 1.5v-.1Z"
        fillRule="nonzero"
      />
      <text fontSize="12" x="177" y="170">
        Start of
      </text>
      <text fontSize="12" x="180" y="183">
        month
      </text>
      <text fontSize="12" x="379" y="170">
        End of
      </text>
      <text fontSize="12" x="380" y="183">
        month
      </text>
      <text fontSize="12" x="67" y="88.63">
        {timeText}
      </text>
    </svg>
  );
}

export default EventsBefore;

EventsBefore.propTypes = {
  timeOption: string.isRequired,
  timeScale: string,
  timeValue: number,
};

EventsBefore.defaultProps = {
  timeScale: null,
  timeValue: null,
};
