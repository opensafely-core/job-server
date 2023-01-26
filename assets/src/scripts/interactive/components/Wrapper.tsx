import * as React from "react";
import { useWizard } from "react-use-wizard";
import { classNames, scrollToTop } from "../utils";

function Wrapper({
  children,
}: {
  children?: React.ReactNode;
}): React.ReactElement {
  const { isFirstStep, isLastStep, previousStep } = useWizard();

  return (
    <main className="min-h-[66vh] flex-grow pb-12 bg-gray-100">
      <div className="container xl:max-w-screen-xl py-4" id="content">
        <div className="mb-6 mt-3 flex flex-col gap-y-4 md:gap-y-2 text-center md:mt-0 md:text-left">
          <h1 className="text-3xl tracking-tight break-words md:text-4xl font-bold text-gray-900">
            Interactive request
          </h1>
          <p className="font-lg text-gray-600">
            Make a new request for an interactive report.
          </p>
        </div>

        <section>
          <div className="bg-white p-6 shadow rounded">
            {!isFirstStep && !isLastStep ? (
              <button
                className={classNames(
                  "text-sm font-semibold underline underline-offset-4 text-gray-600 decoration-gray-300 mb-4 flex -mt-1",
                  "hover:text-oxford-600 hover:decoration-oxford-200",
                  "focus-within:text-oxford-600 focus-within:no-underline focus-within:outline-offset-4 focus-within:outline-oxford-400"
                )}
                onClick={() => {
                  scrollToTop();
                  previousStep();
                }}
                type="button"
              >
                &larr; Back
              </button>
            ) : null}
            {children}
          </div>
        </section>
      </div>
    </main>
  );
}

export default Wrapper;

Wrapper.defaultProps = {
  children: [],
};
