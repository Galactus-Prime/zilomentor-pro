/**
 * Isolated ZiloMentor Pro / Elementor editor smoke test.
 *
 * Launched ONLY by tools/qa_isolated_site.py within an internal Docker network.
 * No real admin credentials, production site, host ports or external requests.
 */
"use strict";

const { chromium } = require("playwright");

const token = process.env.ZMP_QA_EDITOR_TOKEN || "";
const pageId = Number(process.env.ZMP_QA_PAGE_ID || "0");
const base = "http://web:8080";
const result = {
  launched: false,
  navigationCommitted: false,
  authenticatedEditorPage: false,
  panelPresent: false,
  previewPresent: false,
  editorGlobalPresent: false,
  panelContentPresent: false,
  domReady: false,
  frameCount: 0,
  pageErrorCount: 0,
  blockedExternalRequests: 0,
};
let browser = null;

async function main() {
  if (!/^[a-f0-9]{56}$/.test(token) || !Number.isSafeInteger(pageId) || pageId <= 0) {
    throw new Error("Invalid disposable QA token or page ID");
  }

  browser = await chromium.launch({
    headless: true,
    args: [
      "--no-sandbox", "--disable-dev-shm-usage",
      "--disable-background-networking", "--no-first-run",
    ],
    timeout: 15000,
  });
  result.launched = true;

  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
    javaScriptEnabled: true,
  });
  // Prevent external requests from this test instance.
  await context.route("**/*", async route => {
    const req = route.request().url();
    try {
      const url = new URL(req);
      if (url.hostname === "web" && url.port === "8080" && url.protocol === "http:") {
        await route.continue();
      } else {
        result.blockedExternalRequests += 1;
        await route.abort("blockedbyclient");
      }
    } catch {
      result.blockedExternalRequests += 1;
      await route.abort("blockedbyclient");
    }
  });

  const page = await context.newPage();
  page.on("pageerror", () => { result.pageErrorCount += 1; });

  // Navigation commit is intentional: Elementor may request many admin assets
  // and the disposable server need not finish all background activity.
  const loginUrl = base + "/?zmp_qa_editor_login=" + token + "&zmp_qa_page=" + pageId;
  const response = await page.goto(loginUrl, {
    waitUntil: "commit",
    timeout: 18000,
  });
  result.navigationCommitted = !!response;

  // Give the panel a limited chance to initialize, without networkidle waits.
  try {
    await page.locator("#elementor-panel").waitFor({ state: "attached", timeout: 15000 });
  } catch {
    // Record actual DOM state below.
  }
  await page.waitForTimeout(4500);

  const dom = await page.evaluate(() => ({
    title: document.title,
    readyState: document.readyState,
    bodyClass: document.body ? document.body.className : "",
    editorMarker: !!document.querySelector("#elementor-editor-wrapper, #elementor-panel"),
    panelPresent: !!document.querySelector("#elementor-panel"),
    panelChildCount: document.querySelector("#elementor-panel")?.children.length || 0,
    panelControlCount: document.querySelector("#elementor-panel")
      ?.querySelectorAll("button,input,[role=button],[role=tab]").length || 0,
    panelTextLength: document.querySelector("#elementor-panel")?.textContent?.trim().length || 0,
    previewPresent: !!document.querySelector("#elementor-preview, #elementor-preview-iframe"),
    editorGlobalPresent: !!window.elementor,
    panelContentPresent: !!document.querySelector(
      "#elementor-panel-content-wrapper, .elementor-panel-category, .elementor-panel-navigation"
    ),
    loginFormPresent: !!document.querySelector("#loginform"),
  }));

  result.authenticatedEditorPage =
    (dom.title || "").toLowerCase().includes("elementor") && !dom.loginFormPresent;
  result.panelPresent = dom.panelPresent;
  result.previewPresent = dom.previewPresent;
  result.editorGlobalPresent = dom.editorGlobalPresent;
  result.panelContentPresent = dom.panelContentPresent;
  result.panelChildCount = dom.panelChildCount;
  result.panelControlCount = dom.panelControlCount;
  result.panelTextLength = dom.panelTextLength;
  result.domReady = dom.readyState === "interactive" || dom.readyState === "complete";
  result.pageTitle = String(dom.title || "").slice(0, 140);
  result.frameCount = page.frames().length;
  result.domReadyState = dom.readyState;
  // Login tokens, cookie values and page HTML are deliberately never logged.
}

(async () => {
  let exitCode = 0;
  try {
    await main();
  } catch (e) {
    exitCode = 1;
    result.errorCategory = e && e.name ? String(e.name).slice(0, 60) : "UnknownError";
    // Do not log raw errors or URLs because the input URL has a temp token.
  } finally {
    if (browser) {
      try { await browser.close(); } catch { /* cleanup best effort */ }
    }
    console.log("ZMP_EDITOR_JSON=" + JSON.stringify(result));
    process.exitCode = exitCode;
  }
})();
