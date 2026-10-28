import { test, expect } from "@playwright/test";
import { researchOpsCopy, researchStatusCopy } from "../src/locales/researchOps";
import { workflowOpsCopy } from "../src/locales/workflowOps";

for (const lang of ["en", "ru", "uk", "de", "zh-Hant"] as const) {
  test(`Research pilot source, claim, private export and stale state: ${lang}`, async ({ page, context }) => {
    test.setTimeout(90000);
    const c=researchOpsCopy[lang];const studio=workflowOpsCopy[lang];
    const owner="11111111-1111-4111-8111-111111111111";
    const project={id:"22222222-2222-4222-8222-222222222222",owner_user_id:owner,members:{},name:"Research agency",context:{},retention_days:30};
    const source={id:"33333333-3333-4333-8333-333333333333",project_id:project.id,title:"Product source",url:"https://example.org/",status:"unchecked",latest_hash:null as string|null,checked_at:null as string|null,expires_at:"2026-11-27T00:00:00Z"};
    const sources: typeof source[]=[];
    const claims: {id:string;statement:string;excerpt:string;source_hash:string;status:string;reviewer_verdict:string}[]=[];
    const text='Price 10 EUR <img src=x onerror=alert(1)>';
    let checks=0;const errors:string[]=[];
    page.on("pageerror",e=>errors.push(e.message));
    await context.addCookies([{name:"ancap-lang",value:lang,url:test.info().project.use.baseURL as string}]);
    await page.addInitScript(language=>{localStorage.setItem("ancap-lang-v3",language);localStorage.setItem("ancap_cookie_consent_v1",JSON.stringify({necessary:true,analytics:false,marketing:false}));},lang);
    await page.route("**/v1/**",async route=>{
      const path=new URL(route.request().url()).pathname;
      if(path.endsWith("/users/me"))return route.fulfill({json:{id:owner,email:"research-ui@example.test"}});
      if(path.endsWith("/workflow-ops/capabilities"))return route.fulfill({json:{workflow_slugs:[]}});
      if(path.endsWith("/workflow-store/templates"))return route.fulfill({json:{items:[]}});
      if(path.endsWith("/workflow-ops"))return route.fulfill({json:{user_id:owner,is_operator:false,projects:[project],connections:[],automations:[],runs:[]}});
      if(path.endsWith("/research/sources")){sources.push(source);return route.fulfill({status:201,json:source});}
      if(path.endsWith("/check")){
        checks++;source.status=checks===1?"baseline":"content_change_requires_review";source.latest_hash=(checks===1?"a":"b").repeat(64);source.checked_at="2026-10-28T12:00:00Z";
        if(checks>1)for(const claim of claims)claim.status="requires_update";
        return route.fulfill({json:{source,snapshot:{hash:source.latest_hash,text:checks===1?text:"Price 20 EUR"},changes:{items:[]}}});
      }
      if(path.endsWith("/claims")){
        const body=route.request().postDataJSON();expect(body.source_id).toBe(source.id);expect(body.source_hash).toBe("a".repeat(64));
        claims.push({...body,id:"claim-1",status:body.verdict,reviewer_verdict:body.verdict});return route.fulfill({status:201,json:{id:"claim-1"}});
      }
      if(path.endsWith("/research"))return route.fulfill({json:{sources,claims,version_hash:"c".repeat(64),state:"draft_requires_review",delivery_enabled:false}});
      return route.fulfill({json:{items:[]}});
    });
    await page.setViewportSize({width:390,height:844});
    await page.goto("/ai/studio");
    await page.getByRole("navigation",{name:studio.title,exact:true}).getByRole("button",{name:studio.projects,exact:true}).click();
    await page.getByRole("button",{name:project.name,exact:true}).click();
    const panel=page.getByRole("region",{name:c.title});
    await panel.getByLabel(c.titleField,{exact:true}).fill(source.title);
    await panel.getByLabel(c.url,{exact:true}).fill(source.url);
    await panel.getByLabel(c.permission,{exact:true}).fill("Owner approved public source collection");
    await panel.getByRole("button",{name:c.add,exact:true}).click();
    await panel.getByRole("button",{name:c.check,exact:true}).click();
    await expect(panel.locator("pre")).toHaveText(text);
    await expect(panel.locator("pre img")).toHaveCount(0);
    await panel.getByLabel(c.statement,{exact:true}).fill("The source lists 10 EUR");
    await panel.getByLabel(c.excerpt,{exact:true}).fill("Price 10 EUR");
    await panel.getByRole("combobox",{name:c.verdict,exact:true}).selectOption("supported_by_source");
    await panel.getByRole("button",{name:c.save,exact:true}).click();
    await expect(panel.locator("strong").filter({hasText:c.supported})).toBeVisible();
    const downloadPromise=page.waitForEvent("download");
    await panel.getByRole("button",{name:c.export,exact:true}).click();
    const download=await downloadPromise;expect(download.suggestedFilename()).toMatch(/^research-draft-.*\.json$/);
    const stream=await download.createReadStream();const chunks:Buffer[]=[];for await(const chunk of stream!)chunks.push(Buffer.from(chunk));
    const data=JSON.parse(Buffer.concat(chunks).toString());expect(data.state).toBe("draft_requires_review");expect(data.delivery_enabled).toBe(false);
    await panel.getByRole("button",{name:c.check,exact:true}).click();
    await expect(panel.getByText(c.stale,{exact:true})).toBeVisible();
    await expect(panel.getByText(new RegExp(researchStatusCopy[lang][4]))).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    expect(errors).toEqual([]);
    await page.screenshot({path:test.info().outputPath("research-panel.png"),fullPage:true});
  });
}
