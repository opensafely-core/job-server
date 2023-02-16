import React from "react";
import { createRoot } from "react-dom/client";
import { Route, Router, Switch } from "wouter";
import App from "./App";
import { AppData, FormDataProvider } from "./context";
import QueryBuilder from "./pages/build-query";
import FilterRequest from "./pages/filter-request";
import FindCodelists from "./pages/find-codelists";
import PreviewRequest from "./pages/preview-request";
import ReviewQuery from "./pages/review-query";
import ReviewRequest from "./pages/review-request";
import Success from "./pages/success";
import { getAppData } from "./utils";
import ScrollToTop from "./utils/scrollToTop";

const element = document.getElementById("osi");
if (!element) throw new Error("Failed to find the root element");

const root = createRoot(element);
const { dataset } = element;

if (!dataset.events || !dataset.medications)
  throw new Error("Codelist data not provided");
if (!dataset.basePath) throw new Error("Basename not provided");
if (!dataset.csrfToken) throw new Error("CSRF Token not provided");

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
              <Route path="review-query">
                <ReviewQuery />
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
