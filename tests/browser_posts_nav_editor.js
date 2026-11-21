/**
 * Disposable Elementor Pro Nav Menu and Posts widget editing regression.
 * Opens a real authenticated Elementor editor for the isolated fixture,
 * changes the Nav Menu name through its panel, confirms Posts can be
 * selected, and clicks the normal Publish/Update control. No live WordPress.
 */
"use strict";
const {chromium}=require("playwright");
const token=process.env.ZMP_QA_EDITOR_TOKEN||"";
const pageId=Number(process.env.ZMP_QA_PAGE_ID||0);
const updated="ZiloMentor QA Saved Navigation Menu";
const result={
  authenticated:false,navFound:false,postsFound:false,
  navSelected:false,oldMenuNameMatched:false,newMenuNameMatched:false,
  postsSelected:false,saveClicked:false,
  pageErrors:0,httpErrors:0,requestFailures:0,cancelledRequests:0,
  externalBlocked:0,
};
let browser;
async function main(){
  if(!/^[a-f0-9]{56}$/.test(token) || !Number.isSafeInteger(pageId) ||
     pageId<=0 || process.env.ZMP_QA_POSTS_NAV_EDITOR!=="yes")
    throw new Error("Invalid synthetic editor settings");
  browser=await chromium.launch({headless:true,timeout:15000,
    args:["--no-sandbox","--disable-dev-shm-usage","--no-first-run"]});
  const ctx=await browser.newContext({viewport:{width:1366,height:768}});
  await ctx.route("**/*",async route=>{
    try{
      const u=new URL(route.request().url());
      if(u.protocol==="http:"&&u.hostname==="web"&&u.port==="8080"){
        await route.continue();
      }else{result.externalBlocked++;await route.abort("blockedbyclient");}
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
    if(/ERR_ABORTED|NS_BINDING_ABORTED/i.test(reason))
      result.cancelledRequests++;
    else result.requestFailures++;
  }catch{}});
  await page.goto("http://web:8080/?zmp_qa_editor_login="+token+
    "&zmp_qa_page="+pageId,{waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>!!window.elementor&&
    !!document.querySelector("#elementor-panel")&&
    document.querySelectorAll("#elementor-panel button,#elementor-panel input").length>=30,
    null,{timeout:27000,polling:350});
  result.authenticated=(await page.locator("#loginform").count())===0;
  const frame=page.frameLocator("#elementor-preview-iframe");
  const nav=frame.locator('.elementor-widget-nav-menu[data-id="9a0c1d01"]');
  const posts=frame.locator('.elementor-widget-posts[data-id="9a0c1d02"]');
  await nav.waitFor({state:"visible",timeout:15000});
  await posts.waitFor({state:"visible",timeout:15000});
  result.navFound=await nav.count()===1;
  result.postsFound=await posts.count()===1;
  const menuName=page.locator('#elementor-panel input[data-setting="menu_name"]');
  try{
    await nav.click({timeout:7500});
    await menuName.waitFor({state:"visible",timeout:4500});
  }catch{
    try{
      await nav.locator(".elementor-editor-element-edit").first()
        .click({force:true,timeout:6000});
      await menuName.waitFor({state:"visible",timeout:4500});
    }catch{
      try{
        await nav.dblclick({force:true,timeout:6500});
        await menuName.waitFor({state:"visible",timeout:6500});
      }catch{return;}
    }
  }
  result.navSelected=await menuName.isVisible();
  result.oldMenuNameMatched=(await menuName.first().inputValue())==="ZMP Synthetic Menu";
  if(!result.oldMenuNameMatched)return;
  await menuName.first().fill(updated,{timeout:7000});
  await menuName.first().dispatchEvent("change");
  result.newMenuNameMatched=(await menuName.first().inputValue())===updated;
  if(!result.newMenuNameMatched)return;

  try{
    await posts.click({timeout:7500});
    await page.waitForTimeout(1000);
    result.postsSelected=await page.locator(
      "#elementor-panel .elementor-control-section_query,"+
      "#elementor-panel [data-setting='posts_posts_per_page']"
    ).count()>0;
    if(!result.postsSelected){
      await posts.dblclick({force:true,timeout:6500});
      await page.waitForTimeout(1000);
      result.postsSelected=await page.locator(
        "#elementor-panel .elementor-control-section_query,"+
        "#elementor-panel [data-setting='posts_posts_per_page']"
      ).count()>0;
    }
  }catch{
    result.postsSelected=false;
  }
  result.postsDiagnostic=(await page.locator("#elementor-panel")
    .innerText().catch(()=>"")).trim().slice(0,260);

  const buttons=page.getByRole("button",{name:/^(Update|Publish|Save)$/i});
  for(let i=0;i<Math.min(await buttons.count(),8);i++){
    const button=buttons.nth(i);
    if(await button.isVisible()&&await button.isEnabled()){
      try{await button.click({timeout:7500});result.saveClicked=true;break;}catch{}
    }
  }
  await page.waitForTimeout(2400);
}
(async()=>{
  try{await main()}
  catch(e){result.errorCategory=String(e?.name||"unknown").slice(0,60)}
  finally{
    if(browser)try{await browser.close()}catch{}
    console.log("ZMP_POSTS_NAV_EDITOR_JSON="+JSON.stringify(result));
    process.exitCode=(
      result.authenticated&&result.navFound&&result.postsFound&&
      result.navSelected&&result.oldMenuNameMatched&&
      result.newMenuNameMatched&&result.postsSelected&&result.saveClicked&&
      result.pageErrors===0&&result.httpErrors===0&&result.requestFailures===0
    )?0:1;
  }
})();