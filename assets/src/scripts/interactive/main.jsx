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
        <Router base={dataset.basePath.slice(0, -1)}>
          <ScrollToTop />
          <App
            basePath={dataset.basePath}
            csrfToken={dataset.csrfToken}
            events={dataset.events}
            medications={dataset.medications}
          >
            <Switch>
              <Route component={Glossary} path="/" />
              <Route component={FindCodelists} path="/find-codelists" />
              <Route component={QueryBuilder} path="/build-query" />
              <Route component={PreviewRequest} path="/preview-request" />
              <Route component={FilterRequest} path="/filter-request" />
              <Route
                component={AnalysisInformation}
                path="/analysis-information"
              />
              <Route component={ReviewRequest} path="/review-request" />
              <Route path="*">
                <div className="prose">
                  <h2>An error occurred</h2>
                  <p className="lead">Your request was not submitted.</p>
                  <p>
                    Please try again, or{" "}
                    <a href="mailto:team@opensafely.org">
                      email team@opensafely.org
                    </a>
                    .
                  </p>
                </div>
              </Route>
            </Switch>
          </App>
        </Router>
      </FormDataProvider>
    </AppData.Provider>
  </React.StrictMode>,
);
