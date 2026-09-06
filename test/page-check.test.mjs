import test from "node:test";
import assert from "node:assert/strict";
import { getUnsupportedPageReason } from "../src/popup/page-check.js";

test("blocks Chrome internal pages", () => {
  assert.equal(getUnsupportedPageReason("chrome://newtab/"), "browser-page");
  assert.equal(getUnsupportedPageReason("chrome://extensions/"), "browser-page");
  assert.equal(getUnsupportedPageReason("chrome-search://local-ntp/"), "browser-page");
});

test("blocks the Chrome Web Store", () => {
  assert.equal(
    getUnsupportedPageReason("https://chromewebstore.google.com/detail/example"),
    "web-store"
  );
  assert.equal(
    getUnsupportedPageReason("https://chrome.google.com/webstore/detail/example"),
    "web-store"
  );
});

test("blocks extension pages but allows ordinary websites", () => {
  assert.equal(
    getUnsupportedPageReason("chrome-extension://abcdef/popup/index.html"),
    "extension-page"
  );
  assert.equal(getUnsupportedPageReason("https://example.com/article"), null);
});
