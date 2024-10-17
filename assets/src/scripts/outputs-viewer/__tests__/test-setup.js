import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";
import createFetchMock from "vitest-fetch-mock";
import "window-resizeto/polyfill";

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
