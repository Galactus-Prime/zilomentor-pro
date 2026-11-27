"use strict";
// Private disposable WordPress only. No external network or real site data.
const { chromium } = require("playwright");
const id = Number(process.env.ZMP_QA_ICON_PAGE);
const mode = process.env.ZMP_QA_ICON_FORMAT || "fontello";
const formats = {
  fontello: {className:"zmp-qa-edit",family:"zmp-qa-public",code:0xe800,asset:/\/elementor\/custom-icons\/zmp-qa-public(?:-\d+)?\/font\/zmp-qa-public\.woff2$/},
  icomoon: {className:"zmp-untitled-project-zmp-star",family:"zmp-untitled-project",code:0xf000,asset:/\/elementor\/custom-icons\/untitled-project(?:-\d+)?\/fonts\/Untitled\.woff$/},
};
const spec = formats[mode];
const result = { desktop: false, mobile: false, localFontLoaded: false, pageErrors: 0, failedFontRequests: 0 };
(async () => {
  if (!spec || !Number.isSafeInteger(id) || id < 1) throw new Error("Invalid synthetic page");
  const browser = await chromium.launch({headless:true,args:["--no-sandbox","--disable-dev-shm-usage","--disable-background-networking"],timeout:15000});
  try {
    for (const [key,viewport] of [["desktop",{width:1366,height:768}],["mobile",{width:390,height:844}]]) {
      const context = await browser.newContext({viewport});
      await context.route("**/*",route => {
        const url = new URL(route.request().url());
        return url.origin === "http://web:8080" ? route.continue() : route.abort("blockedbyclient");
      });
      const page = await context.newPage();
      let loaded = false;
      page.on("pageerror",()=>result.pageErrors++);
      page.on("response",response=>{
        const url = new URL(response.url());
        if (url.origin === "http://web:8080" && spec.asset.test(url.pathname) && response.ok()) loaded=true;
      });
      page.on("requestfailed",request=>{
        if (request.resourceType()==="font" && request.url().includes("/custom-icons/")) result.failedFontRequests++;
      });
      const response = await page.goto("http://web:8080/?page_id="+id,{waitUntil:"domcontentloaded",timeout:22000});
      const icon=page.locator(".elementor-element-8a0b1c01 ." + spec.className).first();
      await icon.waitFor({state:"visible",timeout:10000});
      const info=await icon.evaluate(async (el, {family,code})=>{
        const style=getComputedStyle(el,"::before");
        await document.fonts.load('16px "'+family+'"',String.fromCodePoint(code));
        await document.fonts.ready;
        const rect=el.getBoundingClientRect();
        return {family:style.fontFamily,content:style.content,visible:rect.width>0&&rect.height>0,loaded:[...document.fonts].some(f=>f.family.replace(/["']/g,"")===family&&f.status==="loaded")};
      }, {family:spec.family,code:spec.code});
      result[key]=response.ok()&&info.visible&&info.loaded&&info.family.includes(spec.family)&&info.content.includes(String.fromCodePoint(spec.code))&&loaded;
      if (key==="desktop") result.localFontLoaded=loaded;
      await context.close();
    }
  } finally { await browser.close(); }
})().catch(e=>{result.error=e.name+":"+e.message.slice(0,200);}).finally(()=>{
  console.log("ZMP_ICON_BROWSER_JSON="+JSON.stringify(result));
  if(!result.desktop||!result.mobile||!result.localFontLoaded||result.pageErrors||result.failedFontRequests)process.exitCode=1;
});
