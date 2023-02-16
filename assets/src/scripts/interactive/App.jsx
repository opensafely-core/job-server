import PropTypes from "prop-types";
import { useLocation } from "wouter";
import { classNames } from "./utils";

function App({ children }) {
  const [location] = useLocation();
  const isFirstPage = location === "/";
  const isLastPage = location === "/success";

  return (
    <main className="min-h-[66vh] flex-grow pb-12 bg-gray-100">
      <div className="mb-6 mt-3 flex flex-col gap-y-2 text-left md:mt-0">
        <h1 className="text-3xl tracking-tight break-words md:text-4xl font-bold text-gray-900">
          Interactive request
        </h1>
        <p className="font-lg text-gray-600">
          Make a new request for an interactive report.
        </p>
      </div>

      <section className="max-w-3xl">
        <div className="bg-white p-6 shadow rounded">
          {!isFirstPage && !isLastPage ? (
            <button
              className={classNames(
                "text-sm font-semibold underline underline-offset-4 text-gray-600 decoration-gray-300 mb-4 flex -mt-1",
                "hover:text-oxford-600 hover:decoration-oxford-200",
                "focus-within:text-oxford-600 focus-within:no-underline focus-within:outline-offset-4 focus-within:outline-oxford-400"
              )}
              onClick={() => window.history.back()}
              type="button"
            >
              &larr; Back
            </button>
          ) : null}
          {children}
        </div>
      </section>
    </main>
  );
}

export default App;

App.propTypes = {
  children: PropTypes.node.isRequired,
};
