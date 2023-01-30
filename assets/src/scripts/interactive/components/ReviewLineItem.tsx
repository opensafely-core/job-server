import React from "react";
import { useWizard } from "react-use-wizard";

function ReviewLineItem({
  title,
  children,
  step,
}: {
  title: string;
  children: React.ReactNode;
  step: number;
}) {
  const { goToStep } = useWizard();

  return (
    <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:py-5">
      <dt className="text-sm font-medium text-gray-600">{title}</dt>
      <dd className="mt-1 flex text-sm text-gray-900 sm:col-span-2 sm:mt-0">
        <span className="flex-grow">{children}</span>
        <span className="ml-4 flex-shrink-0">
          <button
            className="rounded-md bg-white font-medium text-oxford-600 hover:text-oxford-500 focus:outline-none focus:ring-2 focus:ring-oxford-500 focus:ring-offset-2"
            onClick={() => goToStep(step)}
            type="button"
          >
            Edit
          </button>
        </span>
      </dd>
    </div>
  );
}

export default ReviewLineItem;
