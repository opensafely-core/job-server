function EventsAfter({
  timeScale,
  timeValue,
}: {
  timeScale: string | undefined;
  timeValue: number | undefined;
}) {
  return (
    <svg viewBox="0 0 370 240" xmlns="http://www.w3.org/2000/svg">
      <path
        className="stroke-gray-300 fill-none stroke-[3]"
        d="M2 40v120M160 40v120"
      />
      <text
        className="font-sans text-[12px] fill-gray-700"
        textAnchor="left"
        x="0"
        y="175"
      >
        Start of month
      </text>
      <text
        className="font-sans text-[12px] fill-gray-700"
        textAnchor="left"
        x="155"
        y="175"
      >
        End of month
      </text>
      <path
        className="fill-green-600 stroke-green-600 stroke-[3]"
        d="M50.1 150h199.8"
        transform="translate(36.6 -30)"
      />
      <path
        className="fill-green-600 stroke-green-600 stroke-[3]"
        d="m43.4 150 9-4.5L50 150l2.3 4.5-8.9-4.5Zm213.3 0-9 4.5 2.2-4.5-2.3-4.5 9.1 4.5Z"
        transform="translate(36.6 -30)"
      />
      <path
        className="fill-oxford-300 stroke-oxford-300 stroke-[3]"
        d="m80 270 18.2-100"
        transform="rotate(-45 156.229 -54.875)"
      />
      <path
        className="fill-oxford-300 stroke-oxford-300 stroke-[3]"
        d="m99.4 163.3 2.8 9.7-4-3-4.8 1.3 6-8Z"
        transform="rotate(-45 156.229 -54.875)"
      />
      <text
        className="fill-green-600 font-sans text-[12px]"
        textAnchor="middle"
        x="210"
        y="110"
      >
        {timeValue} {timeScale}
      </text>
      <path
        className="fill-none stroke-oxford-300 stroke-[3]"
        d="m280 30-9 90"
        transform="translate(-203.4 -30)"
      />
      <path
        className="fill-oxford-300 stroke-oxford-300 stroke-[3]"
        d="m270.3 126.7-3.6-9.4 4.3 2.6 4.7-1.7-5.4 8.5Z"
        transform="translate(-203.4 -30)"
      />
      <path
        className="stroke-bn-ribbon-600 fill-bn-ribbon-200"
        d="M258 110h5.8l4.2 6 4.2-6h5.8l-7 10 7 10h-5.8l-4.2-6-4.2 6H258l6.7-10-6.7-10Z"
        transform="translate(-203 0)"
      />
    </svg>
  );
}

export default EventsAfter;
