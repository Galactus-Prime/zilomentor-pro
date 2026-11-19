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
  domContentLoadedEvent: false,
  loadEvent: false,
  localRequestsFailed: [],
  localHttpErrors: [],
  localResponseCount: 0,
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
  page.on("domcontentloaded", () => { result.domContentLoadedEvent = true; });
  page.on("load", () => { result.loadEvent = true; });
  page.on("requestfailed", request => {
    try {
      const url = new URL(request.url());
      if (url.hostname === "web" && result.localRequestsFailed.length < 12) {
        result.localRequestsFailed.push(url.pathname.slice(0, 130));
      }
    } catch { /* no raw URLs logged */ }
  });
  page.on("response", response => {
    try {
      const url = new URL(response.url());
      if (url.hostname !== "web") return;
      result.localResponseCount += 1;
      if (response.status() >= 400 && result.localHttpErrors.length < 12) {
        result.localHttpErrors.push({
          path: url.pathname.slice(0, 130),
          status: response.status(),
        });
      }
    } catch { /* no raw URLs logged */ }
  });

  // Navigation commit is intentional: Elementor may request many admin assets
  // and the disposable server need not finish all background activity.
  const loginUrl = base + "/?zmp_qa_editor_login=" + token + "&zmp_qa_page=" + pageId;
  const response = await page.goto(loginUrl, {
    waitUntil: "commit",
    timeout: 18000,
  });
  result.navigationCommitted = !!response;

  // First wait for DOM parsing (not networkidle), then for usable
  // Elementor panel controls. Explicit bounded waits distinguish a
  // genuinely uninitialized editor from snapshotting too early.
  try {
    await page.waitForLoadState("domcontentloaded", { timeout: 14000 });
    result.domContentLoadedWaitPassed = true;
  } catch {
    result.domContentLoadedWaitPassed = false;
  }
  try {
    await page.locator(
      "#elementor-panel button, #elementor-panel input, #elementor-panel [role=button], #elementor-panel [role=tab]"
    ).first().waitFor({ state: "attached", timeout: 17000 });
    result.panelControlWaitPassed = true;
  } catch {
    result.panelControlWaitPassed = false;
  }
  // Presence of the first button is not sufficient for readiness: Elementor
  // may expose a skeletal panel before it loads its widget categories.
  try {
    await page.waitForFunction(() => {
      const panel = document.querySelector("#elementor-panel");
      return !!panel
        && panel.querySelectorAll("button,input,[role=button],[role=tab]").length >= 30
        && (panel.textContent || "").trim().length >= 500;
    }, null, { timeout: 22000, polling: 500 });
    result.panelPopulatedWaitPassed = true;
  } catch {
    result.panelPopulatedWaitPassed = false;
  }
  await page.waitForTimeout(500);

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
    panelTextSample: document.querySelector("#elementor-panel")
      ?.textContent?.trim().slice(0, 150) || "",
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
  result.panelTextSample = dom.panelTextSample;
  result.domReady = dom.readyState === "interactive" || dom.readyState === "complete";
  result.pageTitle = String(dom.title || "").slice(0, 140);
  result.frameCount = page.frames().length;
  result.domReadyState = dom.readyState;

  // Bound, read-only discovery of the actual free Elementor 4.4 responsive
  // controls. No reliance on legacy selectors or guessed editor commands.
  result.responsiveControls = await page.locator("button,[role=button]").evaluateAll(nodes =>
    nodes.filter(node => /responsive|desktop|tablet|mobile/i.test(
      [
        node.getAttribute("aria-label") || "",
        node.getAttribute("title") || "",
        node.getAttribute("data-testid") || "",
        (node.textContent || "").trim().slice(0,70),
      ].join(" ")
    )).slice(0,24).map(node => ({
      tag:node.tagName,
      label:(node.getAttribute("aria-label") || "").slice(0,100),
      title:(node.getAttribute("title") || "").slice(0,100),
      testId:(node.getAttribute("data-testid") || "").slice(0,100),
      css:String(node.className || "").slice(0,130),
      text:(node.textContent || "").trim().slice(0,55),
    }))
  );
  result.responsivePreview = await page.evaluate(() => ({
    outerPreviewWidth:document.querySelector("#elementor-preview")?.clientWidth || 0,
    previewIframeWidth:document.querySelector("#elementor-preview-iframe")?.clientWidth || 0,
    deviceMode:typeof window.elementor?.getCurrentDeviceMode === "function"
      ? window.elementor.getCurrentDeviceMode() : null,
  }));

  // Read-only editor interaction: identify and select the synthetic Heading
  // widget, then inspect control *attributes* (never values/nonces).
  // Try its normal click, Elementor edit handle, and double-click in order.
  result.previewHeadingFound = false;
  result.headingClickCompleted = false;
  result.headingEditHandleFound = false;
  result.headingEditHandleClicked = false;
  result.headingDoubleClicked = false;
  result.titleControlPresent = false;
  result.titleControlMatchesSynthetic = false;
  result.titleInputOutsidePanelPresent = false;
  try {
    const heading = page.frameLocator("#elementor-preview-iframe")
      .locator(".elementor-widget-heading").first();
    await heading.waitFor({ state: "visible", timeout: 9000 });
    result.previewHeadingFound = true;
    result.headingWidgetClass = String(await heading.getAttribute("class") || "").slice(0, 180);
    result.headingWidgetIdPresent = !!await heading.getAttribute("data-id");

    const panelTitle = page.locator(
      '#elementor-panel input[data-setting="title"], ' +
      '#elementor-panel textarea[data-setting="title"]'
    );
    const inspect = async () => {
      const count = await panelTitle.count();
      if (count > 0) {
        result.titleControlPresent = true;
        const value = await panelTitle.first().inputValue();
        result.titleControlMatchesSynthetic =
          value.includes("ZiloMentor Synthetic Heading");
      }
    };
    await heading.click({ timeout: 7000 });
    result.headingClickCompleted = true;
    await page.waitForTimeout(1200);
    await inspect();

    if (!result.titleControlPresent) {
      const handle = heading.locator(
        ".elementor-editor-element-edit, .elementor-editor-element-settings .elementor-editor-element-edit"
      ).first();
      result.headingEditHandleFound = (await handle.count()) > 0;
      if (result.headingEditHandleFound) {
        try {
          await handle.click({ timeout: 5000, force: true });
          result.headingEditHandleClicked = true;
          await page.waitForTimeout(1200);
          await inspect();
        } catch {
          // Record the later panel state without aborting the smoke test.
        }
      }
    }
    if (!result.titleControlPresent && result.headingEditHandleFound) {
      // Direct DOM click, bounded to the synthetic iframe edit handle, rules
      // out Playwright actionability/overlay issues. Still no data is changed.
      try {
        const handle = heading.locator(".elementor-editor-element-edit").first();
        result.editHandleTag = String(await handle.evaluate(el => el.tagName)).slice(0, 25);
        await handle.evaluate(el => el.click());
        result.headingEditHandleDomClick = true;
        await page.waitForTimeout(1600);
        await inspect();
      } catch (err) {
        result.editHandleDomError = err?.name || "UnknownError";
      }
    }
    if (!result.titleControlPresent) {
      try {
        await heading.dblclick({ timeout: 5000 });
        result.headingDoubleClicked = true;
        await page.waitForTimeout(1100);
        await inspect();
      } catch { /* selector or overlay may not permit double clicks */ }
    }

    result.previewEditorModelPresent = await page.evaluate(() =>
      !!(window.elementor && window.elementor.getPreviewView)
    );
    result.titleInputOutsidePanelPresent =
      (await page.locator('input[data-setting="title"],textarea[data-setting="title"]').count()) > 0;
    result.panelTextAfterHeadingClick = String(
      await page.locator("#elementor-panel").innerText({timeout:3000}) || ""
    ).trim().slice(0, 260);
    result.panelInputTypes = await page.locator("#elementor-panel input").evaluateAll(
      elements => elements.slice(0, 15).map(el => ({
        type: String(el.getAttribute("type") || "").slice(0, 30),
        setting: String(el.getAttribute("data-setting") || "").slice(0, 80),
        namePresent: !!el.getAttribute("name"),
      }))
    );

    if (process.env.ZMP_QA_SAVE_TEST === "yes") {
      // Strictly test only the known synthetic Heading in the temporary DB.
      // This variable is supplied by the explicit --verify-editor-save flag
      // in the private QA runner, never on the live WordPress installation.
      result.saveActionCompleted = false;
      if (await heading.getAttribute("data-id") !== "1a2b3c01" ||
          !result.titleControlMatchesSynthetic) {
        result.saveAborted = "wrong-synthetic-heading-or-title";
      } else {
        const title = panelTitle.first();
        const expected = "ZiloMentor QA Saved Heading";
        await title.fill(expected, { timeout: 6500 });
        await title.dispatchEvent("change");
        result.editedTitleInputMatches = (await title.inputValue()) === expected;
        if (!result.editedTitleInputMatches) {
          result.saveAborted = "test-title-not-applied";
        } else {
          await page.waitForTimeout(900);
          // Prefer the actual editor Save/Update/Publish button when present.
          result.saveCandidates = await page.locator("button").evaluateAll(elements =>
            elements.filter(el => /^(update|publish|save)$/i.test(
              (el.textContent || "").trim()
            )).slice(0, 7).map(el => ({
              text: (el.textContent || "").trim().slice(0, 25),
              enabled: !el.disabled,
            }))
          );
          const candidates = page.getByRole("button", { name: /^(Update|Publish|Save)$/i });
          let clicked = false;
          for (let i = 0; i < Math.min(await candidates.count(), 8); i++) {
            const candidate = candidates.nth(i);
            if (await candidate.isVisible() && await candidate.isEnabled()) {
              try {
                await candidate.click({ timeout: 7000 });
                clicked = true;
                result.saveMethod = "editor-ui-button";
                break;
              } catch { /* try the next available toolbar control */ }
            }
          }
          if (!clicked) {
            // Elementor's own document/save/update command, as implemented
            // in the installed free editor. This still tests a real AJAX save.
            try {
              const commandIssued = await page.evaluate(async () => {
                if (!window.$e || typeof window.$e.run !== "function") return false;
                await window.$e.run("document/save/update");
                return true;
              });
              result.saveMethod = "elementor-document-save-update-command";
              result.saveActionCompleted = commandIssued;
            } catch (error) {
              result.saveActionErrorCategory = error?.name || "UnknownError";
            }
          } else {
            result.saveActionCompleted = true;
          }
          await page.waitForTimeout(2100);
        }
      }
    }
  } catch (error) {
    result.headingSelectionErrorCategory =
      error && error.name ? String(error.name).slice(0, 60) : "UnknownError";
  }
  result.headingSelected = result.titleControlMatchesSynthetic;
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
