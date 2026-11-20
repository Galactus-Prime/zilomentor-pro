/**
 * Theme Builder Header and Popup editable-document regression in a disposable WP DB.
 * Opens the REAL Elementor editor for an isolated published template,
 * changes a Heading and clicks its ordinary Publish/Update UI action.
 * Never execute on a production URL, user or database.
 */
"use strict";
const {chromium}=require("playwright");
const token=process.env.ZMP_QA_EDITOR_TOKEN||"";
const templateId=Number(process.env.ZMP_QA_TEMPLATE_ID||process.env.ZMP_QA_HEADER_ID||0);
const kind=process.env.ZMP_QA_TEMPLATE_KIND||"header";
const isPopup=kind==="popup";
const original=isPopup?"ZMP Synthetic Conditional Popup":"ZMP Synthetic Conditional Header";
const updated=isPopup?"ZiloMentor QA Saved Popup":"ZiloMentor QA Saved Header";
const elementId=isPopup?"7a0b1c02":"7a0b1c01";
const result={authenticated:false,headerWidgetFound:false,headingSelected:false,
  originalMatched:false,editedMatched:false,previewUpdated:false,saveClicked:false,
  pageErrors:0,httpErrors:0,requestFailures:0,cancelledRequests:0,externalBlocked:0};
let browser;
async function main(){
  if(!/^[a-f0-9]{56}$/.test(token)||!Number.isSafeInteger(templateId)||
      templateId<=0||!["header","popup"].includes(kind)||
      process.env.ZMP_QA_THEME_SAVE!=="yes")
    throw new Error("Invalid isolated QA input");
  browser=await chromium.launch({headless:true,timeout:15000,
    args:["--no-sandbox","--disable-dev-shm-usage","--no-first-run"]});
  const ctx=await browser.newContext({viewport:{width:1366,height:768}});
  await ctx.route("**/*",async route=>{
    try{const u=new URL(route.request().url());
      if(u.protocol==="http:"&&u.hostname==="web"&&u.port==="8080")
        await route.continue();
      else {result.externalBlocked++;await route.abort("blockedbyclient");}
    }catch{result.externalBlocked++;await route.abort("blockedbyclient");}
  });
  const page=await ctx.newPage();
  page.on("pageerror",()=>result.pageErrors++);
  page.on("response",r=>{try{if(new URL(r.url()).hostname==="web"&&r.status()>=400)result.httpErrors++}catch{}});
  page.on("requestfailed",r=>{try{
    if(new URL(r.url()).hostname!=="web")return;
    const reason=String(r.failure()?.errorText||r.failure()||"");
    if(/ERR_ABORTED/i.test(reason))result.cancelledRequests++;
    else result.requestFailures++;
  }catch{}});
  await page.goto("http://web:8080/?zmp_qa_editor_login="+token+
    "&zmp_qa_page="+templateId,{waitUntil:"domcontentloaded",timeout:28000});
  await page.waitForFunction(()=>!!document.querySelector("#elementor-panel")&&
    !!window.elementor&&document.querySelectorAll("#elementor-panel button,#elementor-panel input").length>=30,
    null,{timeout:26000,polling:450});
  result.authenticated=(await page.locator("#loginform").count())===0;
  const widget=page.frameLocator("#elementor-preview-iframe")
    .locator('.elementor-widget-heading[data-id="'+elementId+'"]');
  await widget.waitFor({state:"visible",timeout:18000});
  result.headerWidgetFound=(await widget.count())===1;
  const input=page.locator('#elementor-panel input[data-setting="title"],#elementor-panel textarea[data-setting="title"]');
  try{
    await widget.click({timeout:7000});
    await input.waitFor({state:"visible",timeout:4000});
  }catch{
    try{
      await widget.locator(".elementor-editor-element-edit").first()
        .click({force:true,timeout:6000});
      await input.waitFor({state:"visible",timeout:7000});
    }catch{}
  }
  if(!(await input.count())||!(await input.isVisible()))return;
  result.headingSelected=true;
  result.originalMatched=(await input.first().inputValue())===original;
  if(!result.originalMatched)return;
  await input.first().fill(updated,{timeout:7000});
  await input.first().dispatchEvent("change");
  result.editedMatched=(await input.first().inputValue())===updated;
  if(!result.editedMatched)return;
  try{
    await widget.getByText(updated,{exact:false}).first().waitFor({state:"visible",timeout:7500});
    result.previewUpdated=true;
  }catch{}
  const buttons=page.getByRole("button",{name:/^(Update|Publish|Save)$/i});
  for(let n=0;n<Math.min(await buttons.count(),8);n++){
    const button=buttons.nth(n);
    if(await button.isVisible()&&await button.isEnabled()){
      try{await button.click({timeout:7500});result.saveClicked=true;break;}catch{}
    }
  }
  await page.waitForTimeout(2400);
}
(async()=>{
  try{await main()}
  catch(e){result.errorCategory=String(e?.name||"UnknownError").slice(0,60)}
  finally{
    if(browser)try{await browser.close()}catch{}
    result.templateKind=kind;
    console.log("ZMP_THEME_SAVE_JSON="+JSON.stringify(result));
    process.exitCode=(
      result.authenticated&&result.headerWidgetFound&&result.headingSelected&&
      result.originalMatched&&result.editedMatched&&result.saveClicked&&
      result.pageErrors===0&&result.httpErrors===0&&result.requestFailures===0
    )?0:1;
  }
})();
