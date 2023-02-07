import React from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import QueryBuilder, { QueryBuilderLoader } from "./pages/build-query";
import ErrorPage from "./pages/error-page";
import FilterRequest, { FilterRequestLoader } from "./pages/filter-request";
import FindCodelists from "./pages/find-codelists";
import PreviewRequest, { PreviewRequestLoader } from "./pages/preview-request";
import ReviewQuery, { ReviewQueryLoader } from "./pages/review-query";
import ReviewRequest, { ReviewRequestLoader } from "./pages/review-request";
import Success, { SuccessLoader } from "./pages/success";
import ScrollToTop from "./utils/scrollToTop";

const element: HTMLElement | null = document.getElementById("osi");
if (!element) throw new Error("Failed to find the root element");

const root = createRoot(element);
const { dataset } = element;
if (!dataset.events || !dataset.medications)
  throw new Error("Codelist data not provided");

if (!dataset.basePath) throw new Error("Basename not provided");
if (!dataset.csrfToken) throw new Error("CSRF Token not provided");

const router = createBrowserRouter(
  [
    {
      path: "/",
      element: (
        <>
          <ScrollToTop />
          <App
            basePath={dataset.basePath}
            csrfToken={dataset.csrfToken}
            events={dataset.events}
            medications={dataset.medications}
          />
        </>
      ),
      errorElement: <ErrorPage />,
      children: [
        {
          index: true,
          element: <FindCodelists />,
        },
        {
          path: "build-query",
          element: <QueryBuilder />,
          loader: QueryBuilderLoader,
        },
        {
          path: "review-query",
          element: <ReviewQuery />,
          loader: ReviewQueryLoader,
        },
        {
          path: "preview-request",
          element: <PreviewRequest />,
          loader: PreviewRequestLoader,
        },
        {
          path: "filter-request",
          element: <FilterRequest />,
          loader: FilterRequestLoader,
        },
        {
          path: "review-request",
          element: <ReviewRequest />,
          loader: ReviewRequestLoader,
        },
        {
          path: "success",
          element: <Success />,
          loader: SuccessLoader,
        },
      ],
    },
  ],
  { basename: dataset.basePath }
);

root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
