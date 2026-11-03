"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

const base = "/workflow-store/robinhood";
type Packet = {chain_id:number; address:string; website:string; description:string; explorer?:string; metadata?:Record<string,string|number>; missing?:string[]};
type Entry = {run_id:string; status:string; version:number; contact:string; comment:string|null; packet:Packet};
const initial = {chain_id:4663, address:"", website:"", description:"", contact:""};
const labels:Record<string,string> = {draft:"Черновик", verified:"Проверено", pending:"На проверке", revision:"Нужна доработка", rejected:"Отклонено", approved:"Одобрено"};
export function ListingForm({id}:{id:string}) {
  const [form,setForm] = useState(initial);
  const [entry,setEntry] = useState<Entry|null>(null);
  const [busy,setBusy] = useState(true);
  const [error,setError] = useState("");
  const path = base + "/" + id;
  useEffect(()=>{
    let active=true;
    apiFetch(path).then((r:Entry|null)=>{if(active){setEntry(r);if(r)setForm({...r.packet,contact:r.contact});}})
      .catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setBusy(false)});
    return ()=>{active=false};
  },[path]);
  async function save(submit:boolean){
    setBusy(true);setError("");
    try {
      const r = await apiFetch(path+(submit?"/submit":""),{method:submit?"POST":"PUT",body:JSON.stringify(submit?{version:entry?.version}:form)});
      setEntry(r);setForm({...r.packet,contact:r.contact});
    } catch(e){setError(String(e))} finally{setBusy(false)}
  }
  const editable=!entry || ["draft","verified","revision"].includes(entry.status);
  const matches=entry && (["address","website","description","chain_id"] as const).every(k=>form[k]===entry.packet[k]) && form.contact===entry.contact;
  return <details id="robinhood-listing" open={typeof window !== "undefined" && window.location.hash === "#robinhood-listing" || undefined} className="my-5 rounded-xl border p-4"><summary>Листинг токена Robinhood Chain</summary>
    <p>Одна оплата запуска включает заявку в ANCAP и пакет для внешней биржи.</p>
    <form onSubmit={e=>{e.preventDefault();void save(false)}}><fieldset disabled={busy||!editable} className="grid gap-2">
      <label>Сеть <select value={form.chain_id} onChange={e=>setForm({...form,chain_id:Number(e.target.value)})}><option value={4663}>Mainnet</option><option value={46630}>Testnet · тестовый режим</option></select></label>
      {([["address","Адрес контракта"],["website","Сайт проекта"],["description","Описание"],["contact","Закрытый контакт заявителя"]] as const).map(([key,label])=><label key={key}>{label} <input required type={key==="website"?"url":"text"} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})}/></label>)}
      {editable && <button>Сохранить и проверить контракт</button>}</fieldset></form>
    {entry && <><p>{labels[entry.status]} · версия {entry.version} {entry.comment}</p><pre className="overflow-auto">{JSON.stringify(entry.packet,null,2)}</pre>
      {entry.status==="verified" && <button disabled={!matches||busy} onClick={()=>save(true)}>Подтвердить и отправить</button>}
      {["pending","approved","rejected","revision"].includes(entry.status) && <a download="exchange-listing.json" href={"data:application/json;charset=utf-8,"+encodeURIComponent(JSON.stringify(entry.packet,null,2))}>Скачать пакет для биржи</a>}</>}
    {error && <p role="alert">{error}</p>}<p><a href="/robinhood-listings">Каталог токенов ANCAP</a></p></details>;
}

export function ListingCatalog(){
  const [items,setItems]=useState<Packet[]>([]);
  const [error,setError]=useState("");
  useEffect(()=>{apiFetch(base+"/catalog").then(setItems).catch(e=>setError(e.message))},[]);
  return <main className="mx-auto max-w-4xl p-8"><h1>Опубликован в каталоге ANCAP</h1><p>Решение о допуске к торгам принимает внешняя биржа.</p>{error && <p role="alert">{error}</p>}
    {items.map(p=><article key={p.address} className="my-4 rounded-xl border p-4"><strong>{p.metadata?.name || p.address}</strong><p>{p.description}</p><a href={p.explorer}>{p.address}</a></article>)}</main>;
}

export function ListingQueue(){
  const [test,setTest]=useState(false);
  const [items,setItems]=useState<Entry[]>([]);
  const [notes,setNotes]=useState<Record<string,string>>({});
  const [error,setError]=useState("");
  useEffect(()=>{let active=true;setItems([]);setError("");apiFetch(base+"/review?testnet="+test).then(rows=>{if(active)setItems(rows)}).catch(e=>{if(active)setError(e.message)});return ()=>{active=false}},[test]);
  async function decide(r:Entry,decision:string){
    try{await apiFetch(base+"/review/"+r.run_id,{method:"POST",body:JSON.stringify({version:r.version,decision,comment:notes[r.run_id]})});setItems(rows=>rows.filter(i=>i.run_id!==r.run_id));setError("")}catch(e){setError(String(e))}
  }
  return <main className="p-8"><h1>Проверка заявок Robinhood Chain</h1><label><input type="checkbox" checked={test} onChange={e=>setTest(e.target.checked)}/> Тестовый режим</label>{error && <p role="alert">{error}</p>}
    {items.map(r=><article key={r.run_id}><pre>{JSON.stringify(r.packet,null,2)}</pre><p>{r.contact}</p><label>Комментарий <input value={notes[r.run_id]||""} onChange={e=>setNotes({...notes,[r.run_id]:e.target.value})}/></label>
      {["approved","revision","rejected"].map(d=><button className="m-2" disabled={!notes[r.run_id]?.trim()} key={d} onClick={()=>decide(r,d)}>{labels[d]}</button>)}</article>)}</main>;
}

