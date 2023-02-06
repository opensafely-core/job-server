import { useRouteError } from "react-router-dom";

export default function ErrorPage() {
  const error: any = useRouteError();

  if (!error) return null;

  // eslint-disable-next-line no-console
  console.error(error);

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
        <div className="bg-white p-6 shadow rounded prose">
          <p className="lead">An error occurred</p>
          <p>
            {error?.status} &mdash;
            {error?.statusText || error?.message || "Unknown error"}
          </p>
        </div>
      </section>
    </main>
  );
}
