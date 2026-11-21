/**
 * Read-only visual and functional canary for the publicly accessible workshop.
 * No logins, checkout, form submission, cart writes or cache-clearing.
 * Run manually before AND after any controlled Pro plugin switch.
 *
 * Docker example:
 *   docker run --rm --network host -e NODE_PATH=/usr/lib/node_modules
 *      -v "$PWD/tests/browser_live_canary.js:/qa/canary.js:ro"
 *      -v "$OUT:/qa/out" --entrypoint node haven-browser-qa:1.62.1 /qa/canary.js
 */
"use strict";
const fs = require("fs");
const { chromium } = require("playwright");
const ORIGIN = "https://itzybitzyworkshop.co.uk";
const OUT = process.env.ZMP_CANARY_OUTPUT || "/qa/out";
const paths = ["/"];
const originHostname = new URL(ORIGIN).hostname;
const results = {origin:ORIGIN,readOnly:true,viewports:[]};
let browser;
async function main() {
  if (!fs.existsSync(OUT) || !fs.statSync(OUT).isDirectory())
    throw new Error("Pre-created QA output directory required");
  browser = await chromium.launch({headless:true,timeout:20000,
    args:["--no-sandbox","--disable-dev-shm-usage","--no-first-run"]});
  for (const preset of [
    {label:"desktop",width:1366,height:768},
    {label:"mobile",width:390,height:844}
  ]) {
    const context = await browser.newContext({viewport:preset,deviceScaleFactor:1,
      reducedMotion:"reduce",ignoreHTTPSErrors:false});
    const page = await context.newPage();
    const events = {pageErrors:0,firstPartyHttpErrors:[],firstPartyRequestFailures:0};
    page.on("pageerror", () => {events.pageErrors++;});
    page.on("response", r => {
      try {
        const u = new URL(r.url());
        if (u.hostname === originHostname && r.status() >= 400 &&
            events.firstPartyHttpErrors.length < 10) {
          events.firstPartyHttpErrors.push({status:r.status(),path:u.pathname.slice(0,95)});
        }
      } catch {}
    });
    page.on("requestfailed", req => {
      try {
        if (new URL(req.url()).hostname !== originHostname) return;
        const reason = String(req.failure()?.errorText || req.failure() || "");
        if (!/ERR_ABORTED/i.test(reason)) events.firstPartyRequestFailures++;
      } catch {}
    });
    for (const path of paths) {
      const r = {label:preset.label,path};
      try {
        const resp = await page.goto(ORIGIN + path,{waitUntil:"domcontentloaded",timeout:65000});
        r.status = resp ? resp.status() : 0;
        await page.waitForTimeout(5500);
        r.dom = await page.evaluate(() => {
          const count = css => document.querySelectorAll(css).length;
          const widgets = [...document.querySelectorAll(".elementor-widget[data-widget_type]")];
          const imgs = [...document.images];
          // Hidden menu placeholders can intentionally lack an image URL.
          // Only an image with an actual source that fails decoding/loading
          // should count as a broken network image.
          const hasImageSource = image => Boolean(
            image.currentSrc || image.getAttribute("src") || image.getAttribute("srcset")
          );
          return {
            titlePresent:document.title.length>0,
            htmlBytes:document.documentElement.outerHTML.length,
            elementorContainers:count(".elementor-container,.e-con"),
            elementorWidgets:widgets.length,
            widgetTypes:[...new Set(widgets.map(el=>el.getAttribute("data-widget_type")))]
              .filter(Boolean).slice(0,45).sort(),
            forms:count("form"),
            menuLinks:count("nav a, .elementor-nav-menu a"),
            images:imgs.length,
            brokenImages:imgs.filter(i=>hasImageSource(i) && i.complete && i.naturalWidth===0).length,
            emptySourceImages:imgs.filter(i=>!hasImageSource(i)).length,
            horizontalOverflow:document.documentElement.scrollWidth>
              document.documentElement.clientWidth+2,
            hasBody:!!document.body && document.body.innerText.length>100,
          };
        });
        await page.screenshot({path:OUT+"/"+preset.label+"-home.png",
          animations:"disabled",timeout:30000});
        r.screenshotWritten = true;
      } catch (error) {
        r.errorCategory = String(error?.name || "UnknownError").slice(0,60);
        r.screenshotWritten = false;
      }
      r.events = events;
      results.viewports.push(r);
    }
    await context.close();
  }
}
(async () => {
  try {await main();}
  catch(error){results.errorCategory=String(error?.name||"UnknownError").slice(0,60);}
  finally {
    if(browser) {try{await browser.close();}catch{}}
    fs.writeFileSync(OUT+"/report.json",JSON.stringify(results,null,2)+"\n");
    console.log("ZMP_LIVE_CANARY_JSON="+JSON.stringify(results));
    process.exitCode=results.viewports.length===2 && results.viewports.every(
      r=>r.status===200 && r.screenshotWritten && r.dom?.hasBody &&
      r.dom.elementorWidgets>0 && r.events.firstPartyHttpErrors.length===0
    ) ? 0 : 1;
  }
})();
