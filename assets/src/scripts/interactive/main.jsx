import React from "react";
import { createRoot } from "react-dom/client";
import { Route, Router, Switch } from "wouter";
import App from "./App";
import { AppData, FormDataProvider } from "./context";
import QueryBuilder from "./pages/build-query";
import FilterRequest from "./pages/filter-request";
import FindCodelists from "./pages/find-codelists";
import PreviewRequest from "./pages/preview-request";
import ReviewRequest from "./pages/review-request";
import Success from "./pages/success";
import { getAppData } from "./utils";
import ScrollToTop from "./utils/scrollToTop";

const element = document.getElementById("osi");
if (!element) throw new Error("Failed to find the root element");

const root = createRoot(element);
const { dataset } = element;

const required = {
  basePath: "Basename",
  csrfToken: "CSRF Token",
  dateEnd: "End date",
  dateStart: "Start date",
  events: "Events codelist data",
  medications: "Medications codelist data",
};

Object.entries(required).map(([key, value]) => {
  if (!dataset[key]) throw new Error(`${value} not proivided`);
  return null;
});

root.render(
  <React.StrictMode>
    <AppData.Provider value={getAppData({ dataset })}>
      <FormDataProvider>
        <Router base={dataset.basePath}>
          <ScrollToTop />
          <App
            basePath={dataset.basePath}
            csrfToken={dataset.csrfToken}
            events={dataset.events}
            medications={dataset.medications}
          >
            <Switch>
              <Route path="/">
                <FindCodelists />
              </Route>
              <Route path="build-query">
                <QueryBuilder />
              </Route>
              <Route path="preview-request">
                <PreviewRequest />
              </Route>
              <Route path="filter-request">
                <FilterRequest />
              </Route>
              <Route path="review-request">
                <ReviewRequest />
              </Route>
              <Route path="success">
                <Success />
              </Route>
              <Route>
                <div className="prose">
                  <p className="lead">An error occurred</p>
                  <p>404 - Page not found</p>
                </div>
              </Route>
            </Switch>
          </App>
        </Router>
      </FormDataProvider>
    </AppData.Provider>
  </React.StrictMode>
);
