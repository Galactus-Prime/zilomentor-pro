/**
 * Isolated Elementor History regression: make a real Heading settings edit,
 * use Elementor's actual document/history/undo and redo commands, Publish,
 * then independently check WordPress serialized Elementor data via WP-CLI.
 * This script refuses to run without a synthetic page/login token and flag.
 */
"use strict";
const {chromium}=require("playwright");
const token=process.env.ZMP_QA_EDITOR_TOKEN||"";
const pageId=Number(process.env.ZMP_QA_PAGE_ID||0);
const initial="ZiloMentor Synthetic Heading";
const updated="ZiloMentor QA History Redo Heading";
const result={
  authenticated:false,headingVisible:false,titleSelected:false,
  initialMatched:false,editApplied:false,undoCommand:false,
  undoReverted:false,redoCommand:false,redoReapplied:false,
  published:false,pageErrors:0,httpErrors:0,localFailures:0,
  cancellations:0,externalBlocked:0,
};
let browser;
async function main(){
  if(!/^[a-f0-9]{56}$/.test(token)||
     !Number.isSafeInteger(pageId)||pageId<=0||
     process.env.ZMP_QA_HISTORY!=="yes")
    throw new Error("Invalid isolated History QA credentials");
  browser=await chromium.launch({headless:true,timeout:15000,
    args:["--no-sandbox","--disable-dev-shm-usage","--no-first-run"]});
  const ctx=await browser.newContext({viewport:{width:1366,height:768}});
  await ctx.route("**/*",async route=>{
    try{
      const u=new URL(route.request().url());
      if(u.protocol==="http:"&&u.hostname==="web"&&u.port==="8080")
        await route.continue();
      else{result.externalBlocked++;await route.abort("blockedbyclient");}
    }catch{result.externalBlocked++;await route.abort("blockedbyclient");}
  });
  const page=await ctx.newPage();
  page.on("pageerror",()=>result.pageErrors++);
  page.on("response",r=>{try{
    if(new URL(r.url()).hostname==="web"&&r.status()>=400)result.httpErrors++;
  }catch{}});
  page.on("requestfailed",r=>{try{
    if(new URL(r.url()).hostname!=="web")return;
    const reason=String(r.failure()?.errorText||r.failure()||"");
    if(/ERR_ABORTED|NS_BINDING_ABORTED/i.test(reason))result.cancellations++;
    else result.localFailures++;
  }catch{}});
  await page.goto("http://web:8080/?zmp_qa_editor_login="+token+
    "&zmp_qa_page="+pageId,{waitUntil:"domcontentloaded",timeout:28000});
  await page.waitForFunction(()=>!!window.elementor&&!!window.$e&&
    !!document.querySelector("#elementor-panel")&&
    document.querySelectorAll("#elementor-panel button,#elementor-panel input").length>=30,
    null,{timeout:24000,polling:400});
  result.authenticated=(await page.locator("#loginform").count())===0;

  const heading=page.frameLocator("#elementor-preview-iframe")
    .locator('.elementor-widget-heading[data-id="1a2b3c01"]');
  await heading.waitFor({state:"visible",timeout:16000});
  result.headingVisible=await heading.count()===1;
  const title=page.locator('#elementor-panel input[data-setting="title"],'+
    '#elementor-panel textarea[data-setting="title"]').first();
  try{
    await heading.click({timeout:7000});
    await title.waitFor({state:"visible",timeout:5000});
  }catch{
    try{
      await heading.locator(".elementor-editor-element-edit").first()
        .click({force:true,timeout:6000});
      await title.waitFor({state:"visible",timeout:5000});
    }catch{
      await heading.dblclick({force:true,timeout:7000});
      await title.waitFor({state:"visible",timeout:6500});
    }
  }
  result.titleSelected=await title.isVisible();
  result.initialMatched=(await title.inputValue())===initial;
  if(!result.initialMatched)return;
  await title.fill(updated,{timeout:8000});
  await title.dispatchEvent("change");
  result.editApplied=(await title.inputValue())===updated;
  if(!result.editApplied)return;
  await page.waitForTimeout(950);

  try{
    const info=await page.evaluate(async()=>{
      const r=await window.$e.run("document/history/undo");
      return {run:true,hasHistory:!!window.elementor.documents.getCurrent().history,
              itemId:r?.originHistoryItemId??null};
    });
    result.undoCommand=info.run&&info.hasHistory;
  }catch(e){result.undoError=String(e?.name||"unknown").slice(0,70);}
  await page.waitForTimeout(850);
  result.undoValue=(await title.inputValue().catch(()=>"")).slice(0,100);
  result.undoReverted=result.undoValue===initial;
  if(!result.undoReverted)return;

  try{
    const info=await page.evaluate(async()=>{
      const r=await window.$e.run("document/history/redo");
      return {run:true,hasHistory:!!window.elementor.documents.getCurrent().history,
              itemId:r?.originHistoryItemId??null};
    });
    result.redoCommand=info.run&&info.hasHistory;
  }catch(e){result.redoError=String(e?.name||"unknown").slice(0,70);}
  await page.waitForTimeout(850);
  result.redoValue=(await title.inputValue().catch(()=>"")).slice(0,100);
  result.redoReapplied=result.redoValue===updated;
  if(!result.redoReapplied)return;
  const buttons=page.getByRole("button",{name:/^(Update|Publish|Save)$/i});
  for(let i=0;i<Math.min(await buttons.count(),8);i++){
    const button=buttons.nth(i);
    if(await button.isVisible()&&await button.isEnabled()){
      try{await button.click({timeout:7000});result.published=true;break;}catch{}
    }
  }
  await page.waitForTimeout(2200);
}
(async()=>{
  try{await main()}
  catch(e){result.errorCategory=String(e?.name||"unknown").slice(0,70)}
  finally{
    if(browser)try{await browser.close()}catch{}
    console.log("ZMP_HISTORY_EDITOR_JSON="+JSON.stringify(result));
    process.exitCode=(
      result.authenticated&&result.headingVisible&&result.titleSelected&&
      result.initialMatched&&result.editApplied&&
      result.undoCommand&&result.undoReverted&&
      result.redoCommand&&result.redoReapplied&&result.published&&
      result.pageErrors===0&&result.httpErrors===0&&result.localFailures===0
    )?0:1;
  }
})();