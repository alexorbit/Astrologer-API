"use strict";
const $=id=>document.getElementById(id);
const key=$("key"),health=$("health"),ready=$("ready"),list=$("resultList"),raw=$("raw"),runStatus=$("runStatus");
const subject={name:"Caso sintético GIROO",city:"São Paulo",nation:"BR",year:1990,month:11,day:10,hour:11,minute:54,latitude:-23.5505,longitude:-46.6333,timezone:"America/Sao_Paulo",houses_system_identifier:"P"};
const endpoint={
 natal:["/api/v6/chart-data/birth-chart",{subject}],
 chart:["/api/v6/chart/birth-chart",{subject,theme:"classic",language:"PT"}],
 moon:["/api/v6/moon-phase",{year:2026,month:11,day:16,hour:12,minute:0,latitude:-23.5505,longitude:-46.6333,timezone:"America/Sao_Paulo"}],
 calendar:["/api/v6/calendar",{start_date:"2026-11-16",end_date:"2026-11-22",include_sun_times:false,include_planetary_hours:false,include_eclipses:false,include_voc:false,include_aspectarian:false,include_sign_periods:false,include_retrograde_periods:false}],
 transits:["/api/v6/transits/aspect-timeline",{subject,start_date:"2026-11-16",end_date:"2026-11-22",step_days:1,refine_exact_moments:false}]
};
let running=false,lastObject=null;
async function post(path,data,auth=true){
 const headers={"Content-Type":"application/json"};
 if(auth)headers["X-API-Key"]=key.value.trim();
 const t0=performance.now();
 const response=await fetch(path,{method:"POST",headers,body:JSON.stringify(data),cache:"no-store",credentials:"omit"});
 let output;try{output=await response.json()}catch{output={message:"Resposta não JSON"}}
 return{status:response.status,ms:Math.round(performance.now()-t0),output};
}
function record(name,result,ok,reason=""){
 const el=document.createElement("div");el.className="result";
 const label=document.createElement("strong");label.textContent=name;
 const state=document.createElement("span");state.className=ok?"pass":"fail";state.textContent=ok?"APROVADO":"FALHOU";
 const duration=document.createElement("span");duration.textContent=result?.ms==null?"—":result.ms+" ms";
 const detail=document.createElement("small");detail.textContent=reason||("HTTP "+result?.status);
 el.append(label,state,duration,detail);list.prepend(el);runStatus.textContent="Último teste: "+name;
 lastObject=result?.output||null;raw.textContent=JSON.stringify(lastObject,null,2);
}
async function probe(){
 for(const [path,node] of [["/health",health],["/ready",ready]]){
  try{const r=await fetch(path,{cache:"no-store",credentials:"omit"});const data=await r.json();const ok=r.ok&&(path==="/health"||data.ready===true||data.status==="ready"||data.status==="OK");
    node.className="status "+(ok?"ok":"fail");
    node.textContent=(path==="/health"?"Saúde: ":"Efemérides: ")+(ok?"OK":"verificar")+" · HTTP "+r.status;
  }catch(e){node.className="status fail";node.textContent="Sem conexão · "+path;}
 }
}
async function run(name){
 if(name!=="auth"&&!key.value.trim()){record(name,null,false,"Informe a chave X-API-Key da instância.");return false}
 try{
  if(name==="auth"){
   const r=await post(...endpoint.natal,false);const ok=r.status===403;
   record("Segurança sem chave",r,ok,"A API deve responder 403 sem autenticação.");return ok;
  }
  const [path,data]=endpoint[name];const r=await post(path,data);
  let ok=r.status===200&&r.output?.status==="OK";
  let summary="HTTP "+r.status;
  if(ok&&name==="natal")ok=Boolean(r.output.chart_data&&JSON.stringify(r.output.chart_data).includes("Sun"));
  if(ok&&name==="moon")ok=Boolean(r.output.moon_phase_overview);
  if(ok&&name==="calendar")ok=Array.isArray(r.output.ingresses)&&Array.isArray(r.output.lunations);
  if(ok&&name==="transits")ok=Array.isArray(r.output.events);
  if(ok&&name==="chart")ok=typeof r.output.chart==="string"&&r.output.chart.includes("<svg");
  if(ok){
   summary=name==="calendar"?"Ingressos: "+r.output.ingresses.length+"; lunações: "+r.output.lunations.length:name==="transits"?"Eventos: "+r.output.events.length:"Dados obtidos sem respostas simuladas.";
  }else{
   summary="HTTP "+r.status+": "+String(r.output?.error_type||r.output?.message||"Formato inesperado").slice(0,200);
  }
  record(name,r,ok,summary);
  if(ok&&name==="chart"){
   const blob=new Blob([r.output.chart],{type:"image/svg+xml"});
   const url=URL.createObjectURL(blob);const img=$("chartImage");if(img.dataset.oldUrl)URL.revokeObjectURL(img.dataset.oldUrl);
   img.src=url;img.dataset.oldUrl=url;$("svgResult").hidden=false;
  }
  return ok;
 }catch(e){record(name,null,false,String(e.message||e).slice(0,180));return false}
}
async function exclusive(fn){
 if(running)return;running=true;
 for(const b of document.querySelectorAll("button[data-test], #runAll"))b.disabled=true;
 try{await fn()}finally{running=false;for(const b of document.querySelectorAll("button[data-test], #runAll"))b.disabled=false;}
}
for(const b of document.querySelectorAll("button[data-test]"))b.addEventListener("click",()=>exclusive(()=>run(b.dataset.test)));
$("runAll").addEventListener("click",()=>exclusive(async()=>{for(const n of ["auth","natal","chart","moon","calendar","transits"])await run(n)}));
$("probe").addEventListener("click",probe);
$("clear").addEventListener("click",()=>{list.replaceChildren();raw.textContent="Nenhuma resposta.";runStatus.textContent="Nenhum teste executado."});
probe();
