const BLOCKED_BROWSER_PROTOCOLS = new Set([
  "chrome:",
  "chrome-search:",
  "chrome-untrusted:",
  "edge:",
  "about:",
  "devtools:",
  "view-source:"
]);

export function getUnsupportedPageReason(rawUrl) {
  if (typeof rawUrl !== "string" || !rawUrl.trim()) return null;

  let url;
  try {
    url = new URL(rawUrl.trim());
  } catch (_) {
    return null;
  }

  const protocol = url.protocol.toLowerCase();
  if (protocol === "chrome-extension:") return "extension-page";
  if (BLOCKED_BROWSER_PROTOCOLS.has(protocol)) return "browser-page";

  const host = url.hostname.toLowerCase();
  if (
    host === "chromewebstore.google.com" ||
    (host === "chrome.google.com" && url.pathname.toLowerCase().startsWith("/webstore"))
  ) {
    return "web-store";
  }

  return null;
}

if (typeof window !== "undefined") {
  window.PokeFollowerPageCheck = { getUnsupportedPageReason };
}
