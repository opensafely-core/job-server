/* eslint-disable import/no-extraneous-dependencies */
import "@testing-library/jest-dom/extend-expect";
import "whatwg-fetch";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./__mocks__/server";

// Establish API mocking before all tests.
beforeAll(() => server.listen());

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
afterEach(() => server.resetHandlers());

// Clean up after the tests are finished.
afterAll(() => server.close());

/**
 * Match Media (react-hot-toast)
 */
window.matchMedia =
  window.matchMedia ||
  function matchMedia() {
    return {
      matches: false,
      addListener() {},
      removeListener() {},
    };
  };

// Fix for image blobs in jsdom
// https://github.com/jsdom/jsdom/issues/1721
function noOp() {
  return "imgSrc";
}

window.URL.createObjectURL = noOp;
