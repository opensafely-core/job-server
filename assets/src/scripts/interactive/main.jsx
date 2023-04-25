import * as Sentry from "@sentry/react";
import React from "react";
import { createRoot } from "react-dom/client";
import { Route, Router, Switch } from "wouter";
import App from "./App";
import { AppData, FormDataProvider } from "./context";
import AnalysisInformation from "./pages/analysis-information";
import QueryBuilder from "./pages/build-query";
import FilterRequest from "./pages/filter-request";
import FindCodelists from "./pages/find-codelists";
import Glossary from "./pages/glossary";
import PreviewRequest from "./pages/preview-request";
import ReviewRequest from "./pages/review-request";
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
  if (!dataset[key]) throw new Error(`${value} not provided`);
  return null;
});

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate: 1.0,
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
                <Glossary />
              </Route>
              <Route path="find-codelists">
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
              <Route path="analysis-information">
                <AnalysisInformation />
              </Route>
              <Route path="review-request">
                <ReviewRequest />
              </Route>
              <Route>
                <div className="prose">
                  <h2>An error occurred</h2>
                  <p className="lead">You request was not submitted.</p>
                  <p>
                    Please try again, or{" "}
                    <a href="mailto:team@opensafely.org">contact support</a>.
                  </p>
                </div>
              </Route>
            </Switch>
          </App>
        </Router>
      </FormDataProvider>
    </AppData.Provider>
  </React.StrictMode>
);
