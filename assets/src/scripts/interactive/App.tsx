import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { usePageData } from "./stores";
import { classNames, getCodelistPageData } from "./utils";

function App({ events, medications }: { events: string; medications: string }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isFirstPage = location.pathname === "/";
  const isLastPage = location.pathname === "/success";

  usePageData.setState({
    pageData: [
      {
        name: "Event",
        id: events,
        codelists: getCodelistPageData(events),
      },
      {
        name: "Medication",
        id: medications,
        codelists: getCodelistPageData(medications),
      },
    ],
  });

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
            {!isFirstPage && !isLastPage ? (
              <button
                className={classNames(
                  "text-sm font-semibold underline underline-offset-4 text-gray-600 decoration-gray-300 mb-4 flex -mt-1",
                  "hover:text-oxford-600 hover:decoration-oxford-200",
                  "focus-within:text-oxford-600 focus-within:no-underline focus-within:outline-offset-4 focus-within:outline-oxford-400"
                )}
                onClick={() => navigate(-1)}
                type="button"
              >
                &larr; Back
              </button>
            ) : null}
            <Outlet />
          </div>
        </section>
      </div>
    </main>
  );
}

export default App;
