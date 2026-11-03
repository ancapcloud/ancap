import {test,expect} from "@playwright/test";

test("prepare, download, review and view a Robinhood listing",async({page})=>{
  const id="12345678-1234-1234-1234-123456789012";
  const slug="exchange-listing-submission-pack";
  const price={amount:"100",currency:"ACP"};
  const owner={id,email:"owner@example.org",display_name:"Owner"};
  const run={id,workflow_slug:slug,title:"Listing",owner_user_id:id,status:"completed",price,payment_currency:"ACP",
    inputs:{},preview:{},result:null,created_at:new Date().toISOString(),receipt:{workflow_slug:slug,status:"completed",quoted_price:price,proof:{},receipt_items:[]}};
  let packet:Record<string,unknown>={},status="",contact="";
  await page.addInitScript(()=>localStorage.setItem("ancap_cookie_consent_v1",JSON.stringify({necessary:true})));
  await page.route("**/v1/**",async route=>{
    const req=route.request(),path=new URL(req.url()).pathname;
    let body:unknown=null;
    if(path.endsWith("/users/me"))body=owner;
    if(path.endsWith("/runs/"+id))body=run;
    if(path.includes("/robinhood/")){
      if(req.method()==="PUT"){
        const {contact:privateContact,...fields}=req.postDataJSON();contact=privateContact;packet={...fields,metadata:{symbol:"RHT"},missing:[]};status="verified";
      }
      if(path.endsWith("/submit"))status="pending";
      if(path.endsWith("/review/"+id))status=req.postDataJSON().decision;
      const row={run_id:id,version:1,status,packet,contact};
      body=path.endsWith("/catalog")?(status==="approved"?[packet]:[]):path.endsWith("/review")?[row]:status?row:null;
    }
    await route.fulfill({contentType:"application/json",body:JSON.stringify(body)});
  });
  await page.goto("/ai/runs/"+id+"#robinhood-listing");
  await page.getByLabel("Адрес контракта").fill("0x"+"ab".repeat(20));
  await page.getByLabel("Сайт проекта").fill("https://example.org");
  await page.getByLabel("Описание",{exact:true}).fill("Browser token example");
  await page.getByLabel("Закрытый контакт заявителя").fill("private@example.org");
  await page.getByText("Сохранить и проверить контракт").click();
  await page.getByText("Подтвердить и отправить").click();
  const download=page.waitForEvent("download");
  await page.getByText("Скачать пакет для биржи").click();
  expect((await download).suggestedFilename()).toBe("exchange-listing.json");
  await page.goto("/admin/robinhood-listings");
  await page.getByLabel("Комментарий").fill("OK");
  await page.getByRole("button",{name:"Одобрено"}).click();
  await expect(page.getByLabel("Комментарий")).toHaveCount(0);
  await page.goto("/robinhood-listings");
  await expect(page.getByText("Browser token example")).toBeVisible();
  await expect(page.getByText("private@example.org")).toHaveCount(0);
});
