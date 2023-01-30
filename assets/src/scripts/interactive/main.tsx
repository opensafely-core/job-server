import React from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import QueryBuilder, { QueryBuilderLoader } from "./pages/build-query";
import FilterRequest from "./pages/filter-request";
import FindCodelists from "./pages/find-codelists";
import PreviewRequest from "./pages/preview-request";
import ReviewQuery, { ReviewQueryLoader } from "./pages/review-query";
import ReviewRequest from "./pages/review-request";
import Success from "./pages/success";

const element: HTMLElement | null = document.getElementById("osi");
if (!element) throw new Error("Failed to find the root element");

const root = createRoot(element);
const { dataset } = element;
if (!dataset.events || !dataset.medications)
  throw new Error("Codelist data not provided");

const router = createBrowserRouter(
  [
    {
      path: "/",
      element: (
        <App events={dataset.events} medications={dataset.medications} />
      ),
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
        },
        {
          path: "filter-request",
          element: <FilterRequest />,
        },
        {
          path: "review-request",
          element: <ReviewRequest />,
        },
        {
          path: "success",
          element: <Success />,
        },
      ],
    },
  ],
  { basename: element.dataset.basePath }
);

root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
