/**
 * Disposable-only Theme Builder/Popup browser behavior regression.
 * QA host launches this in a private Docker network, with no real site data.
 */
"use strict";
const { chromium } = require("playwright");
const targetId = Number(process.env.ZMP_QA_TARGET_ID || 0);
const unrelatedId = Number(process.env.ZMP_QA_UNRELATED_ID || 0);
const popupId = Number(process.env.ZMP_QA_POPUP_ID || 0);
const scrollTargetId = Number(process.env.ZMP_QA_SCROLL_TARGET_ID || 0);
const exitTargetId = Number(process.env.ZMP_QA_EXIT_TARGET_ID || 0);
const scrollPopupId = Number(process.env.ZMP_QA_SCROLL_POPUP_ID || 0);
const exitPopupId = Number(process.env.ZMP_QA_EXIT_POPUP_ID || 0);
const result = {
  loadedTarget: false,
  loadedUnrelated: false,
  headerVisible: false,
  popupApiReady: false,
  popupDocumentRegistered: false,
  popupModalOpened: false,
  popupAutoOpened: false,
  popupAutoOpenedMobile: false,
  popupHeadingVisible: false,
  popupModalClosed: false,
  unrelatedPopupAbsent: false,
  unrelatedHeaderAbsent: false,
  scrollPopupAbsentBeforeScroll: false,
  scrollPopupOpenedByScroll: false,
  exitPopupAbsentBeforeIntent: false,
  exitPopupOpenedByIntent: false,
  unrelatedScrollPopupAbsent: false,
  unrelatedExitPopupAbsent: false,
  pageErrors: 0,
  failedLocalRequests: 0,
  blockedExternalRequests: 0,
};
let browser;
async function main() {
  if (![targetId, unrelatedId, popupId, scrollTargetId, exitTargetId,
    scrollPopupId, exitPopupId].every(x => Number.isSafeInteger(x) && x > 0)) {
    throw new Error("Invalid synthetic test identifiers");
  }
  browser = await chromium.launch({
    headless: true, args: ["--no-sandbox", "--disable-dev-shm-usage",
      "--disable-background-networking", "--no-first-run"], timeout: 15000,
  });
  const context = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  await context.route("**/*", async route => {
    try {
      const u = new URL(route.request().url());
      if (u.protocol === "http:" && u.hostname === "web" && u.port === "8080") {
        await route.continue();
      } else {
        result.blockedExternalRequests++;
        await route.abort("blockedbyclient");
      }
    } catch {
      result.blockedExternalRequests++;
      await route.abort("blockedbyclient");
    }
  });
  const page = await context.newPage();
  page.on("pageerror", () => { result.pageErrors++; });
  page.on("requestfailed", req => {
    try {
      if (new URL(req.url()).hostname === "web") result.failedLocalRequests++;
    } catch { /* no request content logged */ }
  });
  await page.goto("http://web:8080/?page_id=" + targetId,
    { waitUntil: "domcontentloaded", timeout: 22000 });
  result.loadedTarget = true;
  try {
    await page.getByText("ZMP Synthetic Conditional Header").first()
      .waitFor({ state: "visible", timeout: 9000 });
    result.headerVisible = true;
  } catch { /* record failure */ }

  try {
    await page.waitForFunction(id => (
      !!window.elementorProFrontend?.modules?.popup?.showPopup
      && !!window.elementorFrontend?.documentsManager?.documents?.[id]
    ), popupId, { timeout: 22000, polling: 300 });
    result.popupApiReady = true;
    result.popupDocumentRegistered = true;
  } catch {
    result.popupApiReady = await page.evaluate(() =>
      !!window.elementorProFrontend?.modules?.popup?.showPopup);
    result.popupDocumentRegistered = await page.evaluate(id =>
      !!window.elementorFrontend?.documentsManager?.documents?.[id], popupId);
  }
  if (result.popupApiReady && result.popupDocumentRegistered) {
    const modal = page.locator("#elementor-popup-modal-" + popupId);
    try {
      // This must open WITHOUT manually calling showPopup: it exercises the
      // documented On Page Load trigger seeded in the disposable template.
      await modal.waitFor({ state: "visible", timeout: 12000 });
      result.popupAutoOpened = true;
    } catch {
      // Still inspect the manually invoked API separately on failure.
      await page.evaluate(id => window.elementorProFrontend.modules.popup.showPopup({id}), popupId);
    }
    try {
      await modal.waitFor({ state: "visible", timeout: 10000 });
      result.popupModalOpened = true;
      result.popupHeadingVisible = await modal
        .getByText("ZMP Synthetic Conditional Popup").first().isVisible();
      await page.evaluate(id =>
        window.elementorFrontend.documentsManager.documents[id].getModal().hide(), popupId);
      await modal.waitFor({ state: "hidden", timeout: 10000 });
      result.popupModalClosed = true;
    } catch (e) {
      result.modalErrorType = e?.name || "UnknownError";
    }
  }

  // A second isolated browser context avoids test localStorage interfering
  // with the automatic trigger at a mobile viewport.
  const mobileContext = await browser.newContext({viewport:{width:390,height:844}});
  await mobileContext.route("**/*", async route => {
    try {
      const u = new URL(route.request().url());
      if (u.hostname === "web" && u.port === "8080" && u.protocol === "http:") {
        await route.continue();
      } else {
        result.blockedExternalRequests++;
        await route.abort("blockedbyclient");
      }
    } catch {
      result.blockedExternalRequests++;
      await route.abort("blockedbyclient");
    }
  });
  const mobilePage = await mobileContext.newPage();
  await mobilePage.goto("http://web:8080/?page_id=" + targetId,
    {waitUntil:"domcontentloaded",timeout:22000});
  try {
    await mobilePage.locator("#elementor-popup-modal-" + popupId)
      .waitFor({state:"visible",timeout:14000});
    result.popupAutoOpenedMobile = true;
  } catch {
    // Only inspect, do not disguise a failed automatic trigger.
  }
  await mobileContext.close();
  // Independent popup targets prevent the already-passing Page Load trigger
  // from hiding failures in the scrolling or exit-intent implementations.
  // All documents are synthetic; no API is manually called to open a popup.
  async function openTriggerPage(target, popup) {
    const isolated = await browser.newContext({viewport:{width:1366,height:768}});
    await isolated.route("**/*", async route => {
      try {
        const u = new URL(route.request().url());
        if (u.protocol === "http:" && u.hostname === "web" && u.port === "8080") {
          await route.continue();
        } else {
          result.blockedExternalRequests++;
          await route.abort("blockedbyclient");
        }
      } catch {
        result.blockedExternalRequests++;
        await route.abort("blockedbyclient");
      }
    });
    const p = await isolated.newPage();
    p.on("pageerror", () => { result.pageErrors++; });
    p.on("requestfailed", req => {
      try {
        if (new URL(req.url()).hostname === "web") result.failedLocalRequests++;
      } catch { /* avoid reporting sensitive URLs */ }
    });
    await p.goto("http://web:8080/?page_id=" + target,
      {waitUntil:"domcontentloaded",timeout:22000});
    await p.waitForFunction(id => !!window.elementorFrontend?.documentsManager
      ?.documents?.[id], popup, {timeout:17000,polling:250});
    return {context:isolated, page:p,
      modal:p.locator("#elementor-popup-modal-" + popup)};
  }

  const scroll = await openTriggerPage(scrollTargetId, scrollPopupId);
  try {
    // Registration is not activation. The popup must stay closed before
    // scrolling; otherwise an unrelated Page Load trigger may be masking it.
    await scroll.page.waitForTimeout(700);
    result.scrollPopupAbsentBeforeScroll = !(await scroll.modal.isVisible());
    const distance = await scroll.page.evaluate(
      () => Math.max(0, document.documentElement.scrollHeight - innerHeight));
    result.scrollDistanceAvailable = distance > 700;
    if (result.scrollDistanceAvailable && result.scrollPopupAbsentBeforeScroll) {
      await scroll.page.mouse.wheel(0, distance);
      await scroll.page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
      try {
        await scroll.modal.waitFor({state:"visible",timeout:10000});
        result.scrollPopupOpenedByScroll = await scroll.modal
          .getByText("ZMP Synthetic Scroll Popup").first().isVisible();
      } catch { /* leave assertion false */ }
    }
  } finally {
    await scroll.context.close();
  }

  const exit = await openTriggerPage(exitTargetId, exitPopupId);
  try {
    await exit.page.waitForTimeout(700);
    result.exitPopupAbsentBeforeIntent = !(await exit.modal.isVisible());
    if (result.exitPopupAbsentBeforeIntent) {
      // A real pointer leaving the top edge, not a synthetic event or an
      // invocation of the popup API, exercises the browser exit-intent trigger.
      await exit.page.mouse.move(600, 350);
      await exit.page.mouse.move(600, 4, {steps:5});
      await exit.page.mouse.move(600, -30, {steps:3});
      try {
        await exit.modal.waitFor({state:"visible",timeout:10000});
        result.exitPopupOpenedByIntent = await exit.modal
          .getByText("ZMP Synthetic Exit Popup").first().isVisible();
      } catch { /* leave assertion false */ }
    }
  } finally {
    await exit.context.close();
  }

  await page.goto("http://web:8080/?page_id=" + unrelatedId,
    { waitUntil: "domcontentloaded", timeout: 22000 });
  result.loadedUnrelated = true;
  await page.waitForTimeout(1300);
  result.unrelatedPopupAbsent = await page.evaluate(id => (
    !document.querySelector("[data-elementor-id='" + id + "']")
    && !window.elementorFrontend?.documentsManager?.documents?.[id]
  ), popupId);
  result.unrelatedHeaderAbsent =
    !(await page.getByText("ZMP Synthetic Conditional Header").count());
  result.unrelatedScrollPopupAbsent = await page.evaluate(id =>
    !document.querySelector("[data-elementor-id='" + id + "']")
    && !window.elementorFrontend?.documentsManager?.documents?.[id],
  scrollPopupId);
  result.unrelatedExitPopupAbsent = await page.evaluate(id =>
    !document.querySelector("[data-elementor-id='" + id + "']")
    && !window.elementorFrontend?.documentsManager?.documents?.[id],
  exitPopupId);
}
(async () => {
  let exitCode = 0;
  try {
    await main();
  } catch (error) {
    exitCode = 1;
    result.errorType = error?.name || "UnknownError";
  } finally {
    if (browser) { try { await browser.close(); } catch { /* cleanup */ } }
    console.log("ZMP_THEME_POPUP_BROWSER_JSON=" + JSON.stringify(result));
    process.exitCode = exitCode;
  }
})();
