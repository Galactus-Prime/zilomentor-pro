/**
 * Disposable-only Elementor responsive editor mode switching regression.
 * Uses actual control data-testid values observed in Elementor 4.4.1.
 * No page mutations, external requests or production credentials.
 */
"use strict";
const {chromium}=require("playwright");
const token=process.env.ZMP_QA_EDITOR_TOKEN||"";
const pageId=Number(process.env.ZMP_QA_PAGE_ID||0);
const result={authenticated:false,controlsPresent:false,desktopInitiallySelected:false,
  tabletSelected:false,mobileSelected:false,desktopRestored:false,
  tabletWidthValid:false,mobileWidthValid:false,desktopWidthRestored:false,
  headingStillPresent:false,formStillPresent:false,pageErrors:0,httpErrors:0,
  failedLocalRequests:0,cancelledLocalRequests:0,externalBlocked:0,
  dimensions:{}};
let browser;
async function main(){
  if(!/^[a-f0-9]{56}$/.test(token)||!Number.isSafeInteger(pageId)||pageId<1||
      process.env.ZMP_QA_RESPONSIVE!=="yes")
    throw new Error("Invalid isolated editor QA request");
  browser=await chromium.launch({headless:true,timeout:15000,
    args:["--no-sandbox","--disable-dev-shm-usage","--no-first-run"]});
  const ctx=await browser.newContext({viewport:{width:1440,height:900}});
  await ctx.route("**/*",async route=>{
    try{const u=new URL(route.request().url());
      if(u.hostname==="web"&&u.port==="8080"&&u.protocol==="http:"){
        await route.continue();
      }else{result.externalBlocked++;await route.abort("blockedbyclient")}
    }catch{result.externalBlocked++;await route.abort("blockedbyclient")}
  });
  const page=await ctx.newPage();
  page.on("pageerror",()=>result.pageErrors++);
  page.on("response",r=>{try{if(new URL(r.url()).hostname==="web"&&r.status()>=400)result.httpErrors++}catch{}});
  page.on("requestfailed",req=>{try{
    if(new URL(req.url()).hostname!=="web")return;
    const kind=String(req.failure()?.errorText||req.failure()||"");
    if(/ERR_ABORTED/i.test(kind))result.cancelledLocalRequests++;
    else result.failedLocalRequests++;
  }catch{}});
  await page.goto("http://web:8080/?zmp_qa_editor_login="+token+
    "&zmp_qa_page="+pageId,{waitUntil:"domcontentloaded",timeout:28000});
  await page.waitForFunction(()=>!!window.elementor&&
    !!document.querySelector("#elementor-preview-iframe")&&
    document.querySelectorAll("#elementor-panel button,#elementor-panel input").length>=30,
    null,{timeout:26000,polling:500});
  result.authenticated=(await page.locator("#loginform").count())===0;
  const desktop=page.getByTestId("switch-device-to-desktop");
  const tablet=page.getByTestId("switch-device-to-tablet");
  const mobile=page.getByTestId("switch-device-to-mobile");
  result.controlsPresent=(await desktop.count())===1&&
    (await tablet.count())===1&&(await mobile.count())===1;
  if(!result.controlsPresent)return;
  const frame=page.locator("#elementor-preview-iframe");
  const width=async()=>await frame.evaluate(el=>el.clientWidth);
  result.desktopInitiallySelected=(await desktop.getAttribute("aria-selected"))==="true";
  result.dimensions.initial=await width();
  await tablet.click({timeout:7000});
  await page.waitForTimeout(1300);
  result.tabletSelected=(await tablet.getAttribute("aria-selected"))==="true";
  result.dimensions.tablet=await width();
  result.tabletWidthValid=result.dimensions.tablet<result.dimensions.initial&&
    result.dimensions.tablet>=650&&result.dimensions.tablet<=1030;
  await mobile.click({timeout:7000});
  await page.waitForTimeout(1300);
  result.mobileSelected=(await mobile.getAttribute("aria-selected"))==="true";
  result.dimensions.mobile=await width();
  result.mobileWidthValid=result.dimensions.mobile<result.dimensions.tablet&&
    result.dimensions.mobile>=280&&result.dimensions.mobile<=775;
  result.headingStillPresent=await page.frameLocator("#elementor-preview-iframe")
    .locator('.elementor-widget-heading[data-id="1a2b3c01"]').count()===1;
  result.formStillPresent=await page.frameLocator("#elementor-preview-iframe")
    .locator('.elementor-widget-form[data-id="1a2b3c4d"]').count()===1;
  await desktop.click({timeout:7000});
  await page.waitForTimeout(1100);
  result.desktopRestored=(await desktop.getAttribute("aria-selected"))==="true";
  result.dimensions.restored=await width();
  result.desktopWidthRestored=result.dimensions.restored>=result.dimensions.initial-16;
}
(async()=>{
 try{await main()}
 catch(e){result.errorCategory=String(e?.name||"UnknownError").slice(0,60)}
 finally{
   if(browser)try{await browser.close()}catch{}
   console.log("ZMP_RESPONSIVE_JSON="+JSON.stringify(result));
   process.exitCode=(
     result.authenticated&&result.controlsPresent&&result.desktopInitiallySelected&&
     result.tabletSelected&&result.mobileSelected&&result.desktopRestored&&
     result.tabletWidthValid&&result.mobileWidthValid&&result.desktopWidthRestored&&
     result.headingStillPresent&&result.formStillPresent&&
     result.pageErrors===0&&result.httpErrors===0&&result.failedLocalRequests===0
   )?0:1;
 }
})();
