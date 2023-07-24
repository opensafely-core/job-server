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

      <section className="max-w-3xl relative">
        <div
          className={classNames(
            "bg-white p-6 shadow rounded",
            !isFirstPage && !isLastPage ? "pt-12" : null,
          )}
        >
          {!isFirstPage && !isLastPage ? (
            <button
              className={classNames(
                "absolute top-0 left-0 text-sm font-semibold py-1 pl-2 pr-3 flex text-white bg-oxford-800 rounded-br transition-colors",
                "hover:text-oxford-50 hover:bg-oxford-700",
                "focus-within:text-oxford-50 focus-within:bg-oxford-700",
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
