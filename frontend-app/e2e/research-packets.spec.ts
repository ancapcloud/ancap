import {test,expect} from "@playwright/test";
import {researchPacketCopy,researchClientExportCopy} from "../src/locales/researchOps";
import {workflowOpsCopy} from "../src/locales/workflowOps";

for(const lang of ["en","ru","uk","de","zh-Hant"] as const){
  test(`Studio reviews an exact research packet: ${lang}`,async({page,context})=>{
    test.setTimeout(90000);
    const c=workflowOpsCopy[lang],r=researchPacketCopy[lang];
    const owner="11111111-1111-4111-8111-111111111111";
    const pid="22222222-2222-4222-8222-222222222222";
    const sid="33333333-3333-4333-8333-333333333333";
    const aid="44444444-4444-4444-8444-444444444444";
    const opid="55555555-5555-4555-8555-555555555555";
    const source={id:sid,title:"Reviewed source",url:"https://example.org/",status:"baseline",latest_hash:"a".repeat(64),checked_at:"2026-10-28T12:00:00Z",expires_at:"2026-11-27T12:00:00Z"};
    const packet={format:"ancap-research-client-packet/v1",research:{project_id:pid,project_name:"Agency",sources:[source],claims:[]},result:{items:[{summary:"Existing report"}]}};
    const progress:{items:{run_id:string;output:unknown;quality:unknown}[];research_packets?:{version:number;hash:string;packet:unknown}[];research_approval?:{packet_hash:string};reviewed_output?:unknown}={items:[{run_id:"base-run",output:{summary:"Existing report"},quality:{}}]};
    const operation={id:opid,owner_user_id:owner,automation_id:aid,kind:"manual",state:"awaiting_review",cost_acp:"0",review_hash:"1".repeat(64),progress};
    let attachments=0,reviews=0;
    const errors:string[]=[];page.on("pageerror",e=>errors.push(e.message));
    await context.addCookies([{name:"ancap-lang",value:lang,url:test.info().project.use.baseURL as string}]);
    await page.addInitScript(language=>{localStorage.setItem("ancap-lang-v3",language);localStorage.setItem("ancap_cookie_consent_v1",JSON.stringify({necessary:true,analytics:false,marketing:false}));},lang);
    await page.route("**/v1/**",async route=>{
      const path=new URL(route.request().url()).pathname;
      if(path.endsWith("/users/me"))return route.fulfill({json:{id:owner,email:"packet-ui@example.test"}});
      if(path.endsWith("/workflow-ops/capabilities"))return route.fulfill({json:{workflow_slugs:[]}});
      if(path.endsWith("/workflow-store/templates"))return route.fulfill({json:{items:[]}});
      if(path.endsWith("/workflow-ops"))return route.fulfill({json:{user_id:owner,is_operator:false,projects:[{id:pid,owner_user_id:owner,members:{},name:"Agency",context:{},retention_days:30}],automations:[{id:aid,project_id:pid,owner_user_id:owner,name:"Existing workflow",versions:[],published_version:null,enabled:false,interval_minutes:1440,monthly_budget_acp:"0",spent_acp:"0"}],connections:[],runs:[operation]}});
      if(path.endsWith("/research"))return route.fulfill({json:{sources:[source],claims:[],version_hash:"a".repeat(64),state:"draft_requires_review",delivery_enabled:false}});
      if(path.endsWith("/packets")){
        expect(route.request().postDataJSON()).toEqual({operation_id:opid,source_ids:[sid],expected_review_hash:"1".repeat(64)});
        attachments++;progress.research_packets=[{version:1,hash:"2".repeat(64),packet}];operation.review_hash="2".repeat(64);
        return route.fulfill({status:201,json:operation});
      }
      if(path.endsWith("/review")){
        const body=route.request().postDataJSON();expect(body.expected_review_hash).toBe("2".repeat(64));expect(body.decision).toBe("approve");expect(body.edited_output).toEqual({summary:"Human edit"});
        reviews++;operation.state="approved";progress.research_approval={packet_hash:"3".repeat(64)};
        progress.reviewed_output={...packet,result:body.edited_output};
        return route.fulfill({json:operation});
      }
      return route.fulfill({json:{items:[]}});
    });
    await page.setViewportSize({width:390,height:844});await page.goto("/ai/studio");
    const nav=page.getByRole("navigation",{name:c.title,exact:true});
    await nav.getByRole("button",{name:c.projects,exact:true}).click();await page.getByRole("button",{name:"Agency",exact:true}).click();
    await page.getByRole("combobox",{name:r.report,exact:true}).selectOption(opid);
    await page.getByRole("button",{name:r.attach,exact:true}).click();await expect.poll(()=>attachments).toBe(1);
    await nav.getByRole("button",{name:c.runs,exact:true}).click();
    await expect(page.locator("details").filter({hasText:r.title}).locator("pre")).toContainText("Reviewed source");
    await page.getByLabel(c.edited,{exact:true}).fill('{"summary":"Human edit"}');
    await page.getByRole("button",{name:c.approve,exact:true}).click();await expect.poll(()=>reviews).toBe(1);
    await expect(page.getByRole("button",{name:c.approve,exact:true})).toHaveCount(0);
    const pendingDownload=page.waitForEvent("download");await page.getByRole("button",{name:researchClientExportCopy[lang],exact:true}).click();
    const download=await pendingDownload;expect(download.suggestedFilename()).toMatch(/^research-client-packet-/);
    const stream=await download.createReadStream();const chunks:Buffer[]=[];for await(const chunk of stream!)chunks.push(Buffer.from(chunk));
    const exported=JSON.parse(Buffer.concat(chunks).toString());expect(exported.format).toBe("ancap-research-client-packet/v1");expect(exported.result).toEqual({summary:"Human edit"});expect(exported.owner_user_id).toBeUndefined();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    expect(errors).toEqual([]);
  });
}
