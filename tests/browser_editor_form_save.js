/**
 * Opt-in, disposable-only Elementor Pro Form editor persistence regression.
 *
 * Invoked exclusively by --verify-editor-form-save in the private Nginx/FPM QA
 * harness, with synthetic page/user/database. Never use against a real site.
 * Only booleans and bounded diagnostic categories are logged, not auth data.
 */
"use strict";
const { chromium } = require("playwright");
const token = process.env.ZMP_QA_EDITOR_TOKEN || "";
const pageId = Number(process.env.ZMP_QA_PAGE_ID || 0);
const expectedId = "1a2b3c4d";
const original = "ZiloMentor Synthetic Form";
const updated = "ZiloMentor QA Saved Form";
const result = {
  authenticated: false,
  proFormFound: false,
  proFormSelected: false,
  initialFormNameMatched: false,
  editedFormNameMatched: false,
  previewNameUpdated: false,
  actualSaveButtonClicked: false,
  pageErrors: 0,
  failedLocalRequests: 0,
  localHttpErrors: 0,
  blockedExternalRequests: 0,
};
let browser;
async function main() {
  if (!/^[a-f0-9]{56}$/.test(token) ||
      !Number.isSafeInteger(pageId) || pageId < 1 ||
      process.env.ZMP_QA_FORM_SAVE !== "yes") {
    throw new Error("Invalid disposable QA input");
  }
  browser = await chromium.launch({headless:true,timeout:15000,
    args:["--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--no-first-run"]});
  const context = await browser.newContext({viewport:{width:1366,height:768}});
  await context.route("**/*", async route => {
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
  const page = await context.newPage();
  page.on("pageerror", () => { result.pageErrors++; });
  page.on("requestfailed", req => {
    try {
      if (new URL(req.url()).hostname === "web") result.failedLocalRequests++;
    } catch { /* no raw URL logged */ }
  });
  page.on("response", response => {
    try {
      if (new URL(response.url()).hostname === "web" && response.status() >= 400)
        result.localHttpErrors++;
    } catch { /* no URL logged */ }
  });

  await page.goto("http://web:8080/?zmp_qa_editor_login=" + token +
    "&zmp_qa_page=" + pageId, {waitUntil:"domcontentloaded",timeout:25000});
  await page.waitForFunction(() => !!window.elementor &&
    !!document.querySelector("#elementor-panel") &&
    document.querySelectorAll("#elementor-panel button,#elementor-panel input").length >= 30,
    null, {timeout:23000,polling:350});
  result.authenticated = !await page.locator("#loginform").count();

  const widget = page.frameLocator("#elementor-preview-iframe")
    .locator('.elementor-widget-form[data-id="' + expectedId + '"]');
  await widget.waitFor({state:"visible",timeout:13000});
  result.proFormFound = await widget.count() === 1;
  const input = page.locator('#elementor-panel input[data-setting="form_name"]');
  try {
    // A click inside the Form might focus its email field instead of
    // selecting the Elementor widget. The edit handle is the safer fallback.
    await widget.click({timeout:6500});
    await input.waitFor({state:"visible",timeout:3500});
  } catch {
    try {
      await widget.locator(".elementor-editor-element-edit").first()
        .click({timeout:6000,force:true});
      await input.waitFor({state:"visible",timeout:7000});
    } catch {
      // Leave the test result false rather than editing a different widget.
    }
  }
  if (await input.count() !== 1 || !await input.isVisible()) return;
  result.proFormSelected = true;
  result.initialFormNameMatched = (await input.inputValue()) === original;
  if (!result.initialFormNameMatched) return;
  await input.fill(updated,{timeout:7500});
  await input.dispatchEvent("change");
  result.editedFormNameMatched = (await input.inputValue()) === updated;
  if (!result.editedFormNameMatched) return;
  try {
    await widget.locator('form[name="' + updated + '"]')
      .waitFor({state:"attached",timeout:6500});
    result.previewNameUpdated = true;
  } catch { /* persisted server check remains authoritative */ }

  // Require a real visible Elementor Publish/Update button and an actual
  // click. Never silently replace this with a direct WordPress meta write.
  const candidates = page.getByRole("button",{name:/^(Update|Publish|Save)$/i});
  for (let i = 0; i < Math.min(await candidates.count(), 8); i++) {
    const candidate = candidates.nth(i);
    if (await candidate.isVisible() && await candidate.isEnabled()) {
      try {
        await candidate.click({timeout:7000});
        result.actualSaveButtonClicked = true;
        break;
      } catch { /* allow another visible editor button */ }
    }
  }
  await page.waitForTimeout(2300);
}
(async () => {
  try { await main(); }
  catch (e) { result.errorCategory = String(e?.name || "UnknownError").slice(0,60); }
  finally {
    if (browser) { try { await browser.close(); } catch { /* cleanup */ } }
    console.log("ZMP_FORM_SAVE_JSON=" + JSON.stringify(result));
    process.exitCode = result.authenticated && result.proFormFound &&
      result.proFormSelected && result.initialFormNameMatched &&
      result.editedFormNameMatched && result.actualSaveButtonClicked &&
      result.pageErrors === 0 && result.failedLocalRequests === 0 &&
      result.localHttpErrors === 0 ? 0 : 1;
  }
})();
