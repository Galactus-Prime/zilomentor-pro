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
const testFieldRepeater = process.env.ZMP_QA_FORM_FIELDS === "yes";
const updatedFieldLabel = "ZiloMentor QA Saved Email Label";
const result = {
  authenticated: false,
  proFormFound: false,
  proFormSelected: false,
  initialFormNameMatched: false,
  editedFormNameMatched: false,
  previewNameUpdated: false,
  actualSaveButtonClicked: false,
  repeaterSectionFound: false,
  repeaterRowOpened: false,
  repeaterLabelVisible: false,
  repeaterLabelChanged: false,
  pageErrors: 0,
  failedLocalRequests: 0,
  cancelledLocalRequests: 0,
  failedLocalRequestKinds: [],
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
      if (new URL(req.url()).hostname !== "web") return;
      const raw = req.failure();
      const reason = typeof raw === "string" ? raw :
        String(raw?.errorText || "unknown");
      const kind = reason.slice(0, 60);
      // Chromium normally aborts in-flight WP admin-ajax requests when the
      // editor replaces views/navigates. A cancelled request is not a
      // network/server failure, but we record its category for diagnosis.
      if (/ERR_ABORTED|NS_BINDING_ABORTED/i.test(kind)) {
        result.cancelledLocalRequests++;
      } else {
        result.failedLocalRequests++;
      }
      if (result.failedLocalRequestKinds.length < 8) {
        result.failedLocalRequestKinds.push({
          path: new URL(req.url()).pathname.slice(0, 90),
          kind,
        });
      }
    } catch { /* never log the raw URL or any auth token */ }
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
  if (testFieldRepeater) {
    // The Elementor Pro Form editor's actual repeater UI is more than
    // the form-name text input. Expand the existing synthetic email row,
    // edit its visible label and persist the same Widget via Publish.
    const repeater = page.locator(
      '#elementor-panel .elementor-control-form_fields'
    ).first();
    result.repeaterSectionFound = await repeater.count() === 1;
    if (result.repeaterSectionFound) {
      try {
        const row = repeater.locator(
          '.elementor-repeater-row-controls, .elementor-repeater-row-item-title'
        ).first();
        await row.click({timeout:5500,force:true});
        result.repeaterRowOpened = true;
      } catch {
        result.repeaterDiagnostic = (await repeater.innerText().catch(()=>""))
          .trim().slice(0,200);
      }
    }
    const fieldLabel = page.locator(
      '#elementor-panel input[data-setting="field_label"]'
    ).first();
    try {
      await fieldLabel.waitFor({state:"visible",timeout:5500});
      result.repeaterLabelVisible = true;
      await fieldLabel.fill(updatedFieldLabel,{timeout:6500});
      await fieldLabel.dispatchEvent("change");
      result.repeaterLabelChanged =
        (await fieldLabel.inputValue()) === updatedFieldLabel;
    } catch {
      result.repeaterPanelDiagnostic = (await page.locator("#elementor-panel")
        .innerText().catch(()=>"")).trim().slice(0,280);
    }
    if (!result.repeaterLabelChanged) return;
  }

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
      (!testFieldRepeater || (result.repeaterSectionFound &&
        result.repeaterRowOpened && result.repeaterLabelVisible &&
        result.repeaterLabelChanged)) &&
      result.pageErrors === 0 && result.failedLocalRequests === 0 &&
      result.localHttpErrors === 0 ? 0 : 1;
  }
})();
