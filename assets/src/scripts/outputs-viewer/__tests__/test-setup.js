/* eslint-disable import/no-extraneous-dependencies */
import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";
import createFetchMock from "vitest-fetch-mock";
import "window-resizeto/polyfill";

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

/**
 * Fake fetch for Vite
 */
const fetchMocker = createFetchMock(vi);
fetchMocker.enableMocks();

beforeEach(() => {
  fetch.resetMocks();
});
