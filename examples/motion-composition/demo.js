"use strict";
const NS="http://www.w3.org/2000/svg";
const reduce=matchMedia("(prefers-reduced-motion: reduce)");
const blue="#31577d",brick="#8c4536",paper="#fdfdfd";
const fmt=new Intl.NumberFormat("zh-CN",{maximumFractionDigits:1});
const readRatio=(n,d)=>fmt.format(n/d*100)+"%";
const attrs=(e,d)=>{for(const [k,v] of Object.entries(d))e.setAttribute(k,v);};
const step=(n,from,to)=>Math.max(0,Math.min(1,(n-from)/(to-from)));
function atom(parent,kind,properties,text){
  const el=document.createElementNS(NS,kind);
  attrs(el,properties);
  if(text!==undefined)el.textContent=text;
  parent.append(el);return el;
}
function svgText(parent,x,y,text,rest={}){
  return atom(parent,"text",{x,y,...rest},text);
}
function line(parent,x1,y1,x2,y2,rest={}){
  return atom(parent,"line",{x1,y1,x2,y2,...rest});
}
function activate(section,labels,scenes,descriptions,paint,options={}){
  const status=section.querySelector(".status");
  const choices=section.querySelector(".choices");
  const figure=section.querySelector("figure");
  const svg=section.querySelector("svg");
  let index=0,autoTimer=null,locked=false,entered=false;
  const switches=labels.map((label,i)=>{
    const b=document.createElement("button");b.type="button";b.textContent=label;
    b.addEventListener("click",()=>{
      locked=true;
      clearTimeout(autoTimer);
      status.setAttribute("aria-live","polite");
      choose(i);
    });
    choices.append(b);return b;
  });
  function presentation(i){
    switches.forEach((b,j)=>b.setAttribute("aria-pressed",String(i===j)));
  }
  const controller=ChartMotion.create({
    scene:scenes[0],duration:options.duration||860,
    paint(state,info){
      const moving=info.phase==="start"||info.phase==="transition";
      figure.dataset.phase=info.phase;
      paint(state,moving);
      if(moving&&info.meta!==undefined){
        status.textContent="正在切换："+labels[info.meta]+"。";
      }else if(!moving){
        status.textContent=descriptions[index];
        figure.dataset.settled=index;
      }
    }
  });
  presentation(0);
  function choose(i){
    index=i;presentation(i);
    figure.dataset.requested=i;
    controller.to(scenes[i],{meta:i});
    if(!controller.isRunning())status.textContent=descriptions[i];
  }
  if("IntersectionObserver" in window){
    const observer=new IntersectionObserver(entries=>{
      if(entered||!entries.some(e=>e.isIntersecting&&e.intersectionRatio>=.64))return;
      entered=true;observer.disconnect();
      if(locked||reduce.matches)return;
      autoTimer=setTimeout(()=>{
        choose(1);
        autoTimer=setTimeout(()=>choose(2),options.hold||1900);
      },options.initialWait||1150);
    },{threshold:.64});
    observer.observe(svg);
  }
  const stopAuto=()=>{clearTimeout(autoTimer);locked=true;};
  reduce.addEventListener("change",event=>{if(event.matches)stopAuto();});
  window.addEventListener("beforeprint",stopAuto);
}
function orders(){
  const section=document.getElementById("orders"),root=section.querySelector("svg");
  const byGroup=[
    {name:"常规线",color:blue,values:[5,7,8,9,11,12,13,14,15,18,21,29]},
    {name:"加急线",color:brick,values:[8,12,16,18,19,20,22,23,25,27,31,37]}
  ];
  const data=byGroup.flatMap((g,j)=>g.values.map((value,i)=>({id:(j?"E":"S")+String(i+1).padStart(2,"0"),
    value,j,color:g.color,name:g.name})));
  const x=v=>70+v/40*616;
  const baseY=227,cellSize=18;
  const fill=atom(root,"rect",{x:x(20),y:35,width:x(40)-x(20),height:baseY-35,fill:"#f2e7e3",opacity:0});
  const raw=atom(root,"g",{});
  const bins=atom(root,"g",{opacity:0});
  for(const [i,g] of byGroup.entries()){
    const yy=88+i*90;line(raw,x(0),yy,x(40),yy,{class:"grid"});
    svgText(raw,67,yy+4,g.name,{"text-anchor":"end",class:"quiet"});
  }
  for(const n of [0,2,4,6,8]){
    const yy=baseY-n*cellSize;
    line(bins,x(0),yy,x(40),yy,{class:"grid"});
    svgText(bins,61,yy+4,n,{"text-anchor":"end",class:"quiet"});
  }
  svgText(bins,61,56,"单／组",{"text-anchor":"end",class:"quiet"});
  for(const v of [0,10,20,30,40]){
    line(root,x(v),230,x(v),236,{class:"grid"});
    svgText(root,x(v),254,v,{"text-anchor":"middle",class:"quiet"});
  }
  svgText(root,704,254,"分钟",{class:"quiet"});
  const target=atom(root,"g",{opacity:0});
  line(target,x(20),35,x(20),227,{stroke:brick,"stroke-width":1.5,"stroke-dasharray":"5 4"});
  svgText(target,x(20)+9,32,"20 分钟及以上",{class:"strong"});
  const points=new Map();
  const occupied=new Map();
  const scene1={frame:{raw:1,bins:0,focus:0}};
  const scene2={frame:{raw:0,bins:1,focus:0}};
  const scene3={frame:{raw:0,bins:1,focus:1}};
  for(const [i,d] of data.entries()){
    const yy=88+d.j*90+(i%3-1)*12;
    const p=atom(root,"circle",{cx:x(d.value),cy:yy,r:7,fill:d.j?paper:d.color,
      stroke:d.j?d.color:paper,"stroke-width":d.j?2.2:1.3,"data-id":d.id});
    atom(p,"title",{},d.id+"，"+d.name+"，"+d.value+" 分钟");
    points.set(d.id,p);
    const bin=Math.min(3,Math.floor(d.value/10));
    const key=d.j*4+bin;
    const spot=occupied.get(key)||0;occupied.set(key,spot+1);
    const binX=x(bin*10+5)+(d.j===0?-14:14);
    const binY=baseY-10-spot*cellSize;
    scene1[d.id]={x:x(d.value),y:yy};
    scene2[d.id]={x:binX,y:binY};
    scene3[d.id]={x:binX,y:binY};
  }
  const less20=data.filter(d=>d.value<20).length, atleast20=data.length-less20;
  const delayed=byGroup.map((g,i)=>data.filter(d=>d.j===i&&d.value>=20).length);
  section.querySelector(".records").textContent=data.map(d=>[d.id,d.name,d.value+" 分钟"].join(" · ")).join("\n");
  const key=atom(root,"g",{});
  for(const [index,group] of byGroup.entries()){
    const xx=486+index*104;
    atom(key,"circle",{cx:xx,cy:19,r:5,fill:index?paper:group.color,stroke:group.color,"stroke-width":1.6});
    svgText(key,xx+10,23,group.name,{class:"quiet"});
  }
  activate(section,["逐笔记录","按 10 分钟聚合","查看超限订单"],[scene1,scene2,scene3],
    ["24 笔独立记录。点的位置表示实际等待时长。",
     "10–20 分钟箱最多，共 "+(occupied.get(1)+occupied.get(5))+" 笔。每箱包含起点，不含上限，最后一箱含 40。 ",
     "达到 20 分钟的有 "+atleast20+"/24 笔。常规线 "+delayed[0]+"/12，加急线 "+delayed[1]+"/12。"],(state,moving)=>{
      const f=state.get("frame");
      attrs(raw,{opacity:moving&&f.raw<.98?0:f.raw});
      attrs(bins,{opacity:moving&&f.bins<.98?0:f.bins});
      attrs(fill,{opacity:f.focus});attrs(target,{opacity:f.focus});
      for(const d of data){
        const p=state.get(d.id),el=points.get(d.id);
        attrs(el,{cx:p.x,cy:p.y,opacity:d.value<20?1-f.focus*.58:1,
          r:7+(d.value>=20?f.focus*1.5:0)});
      }
    });
}
function routes(){
  const section=document.getElementById("routes"),root=section.querySelector("svg");
  const routes=[
    {count:64,nodes:["接单","库存核对","出库"]},
    {count:22,nodes:["接单","库存核对","补货","出库"]},
    {count:14,nodes:["接单","库存核对","补货","待补货"]}
  ];
  const edges=[
    {a:"接单",b:"库存核对",key:"incoming",d:"M140 76 H242",lx:188,ly:60},
    {a:"库存核对",b:"出库",key:"direct",d:"M402 76 H575",lx:483,ly:59},
    {a:"库存核对",b:"补货",key:"short",d:"M319 100 V164",lx:342,ly:138},
    {a:"补货",b:"出库",key:"filled",d:"M401 184 C500 184 505 107 575 91",lx:488,ly:122},
    {a:"补货",b:"待补货",key:"pending",d:"M402 196 H575",lx:490,ly:219}
  ];
  const counts=new Map(edges.map(e=>[e.key,routes.filter(r=>r.nodes.some((node,i)=>node===e.a&&r.nodes[i+1]===e.b)).reduce((s,r)=>s+r.count,0)]));
  const defs=atom(root,"defs",{});
  const arrow=atom(defs,"marker",{id:"process-arrow",viewBox:"0 0 10 10",refX:9,refY:5,markerWidth:6,markerHeight:6,orient:"auto-start-reverse"});
  atom(arrow,"path",{d:"M0 0 L10 5 L0 10 z",fill:"#667584"});
  const ink=new Map();
  for(const e of edges){
    atom(root,"path",{d:e.d,fill:"none",stroke:"#78828b","stroke-width":1.3,"marker-end":"url(#process-arrow)"});
    const historic=atom(root,"path",{d:e.d,fill:"none",stroke:e.key==="pending"?brick:blue,
      "stroke-linecap":"round","stroke-width":counts.get(e.key)*.16,
      pathLength:1000,"stroke-dasharray":"1000 1000","data-edge":e.key});
    const shine=atom(root,"path",{d:e.d,fill:"none",stroke:e.key==="pending"?"#c78466":"#89a7c2","stroke-width":2.5,
      "stroke-linecap":"round",pathLength:1000,"stroke-dasharray":"58 1200",opacity:0});
    const text=svgText(root,e.lx,e.ly,counts.get(e.key)+" 单",{"text-anchor":"middle",class:"strong",opacity:0});
    ink.set(e.key,{historic,shine,text});
  }
  for(const [name,x,y,w] of [["接单",45,53,96],["库存核对",242,53,159],["出库",575,53,110],
    ["补货",242,164,159],["待补货",575,164,110]]){
    atom(root,"rect",{x,y,width:w,height:46,fill:name==="待补货"?"#f0e5e1":paper,stroke:"#65717b","stroke-width":1.2});
    svgText(root,x+w/2,y+28,name,{"text-anchor":"middle",class:"strong"});
  }
  svgText(root,431,97,"库存足够",{class:"quiet"});
  svgText(root,342,118,"库存不足",{class:"quiet"});
  svgText(root,490,239,"周末仍未到货",{"text-anchor":"middle",class:"quiet"});
  svgText(root,527,157,"补货后到库",{class:"quiet"});
  const start={};
  const overview={};
  const focus={};
  for(const [i,e] of edges.entries()){
    start[e.key]={trace:0,focus:1};
    overview[e.key]={trace:1,focus:1};
    focus[e.key]={trace:1,focus:i<=1?.24:1};
  }
  const total=routes.reduce((s,r)=>s+r.count,0);
  const restock=counts.get("short"),back=counts.get("filled");
  section.querySelector(".records").textContent=routes.map(r=>r.nodes.join(" → ")+" · "+r.count+" 单").join("\n")+
    "\n批次共 "+total+" 单，补货环节共 "+restock+" 单。";
  activate(section,["先读流程规则","叠加实际订单","聚焦补货分支"],[start,overview,focus],
    ["库存足够直接出库。库存不足进入补货，补货后出库，周末仍缺货的继续等待。",
     total+" 单中，"+counts.get("direct")+" 单直接出库，"+restock+" 单进入补货。合计 "+(counts.get("direct")+back)+" 单出库。",
     "补货分支 "+restock+" 单中，"+back+" 单已出库（"+readRatio(back,restock)+"），"+counts.get("pending")+" 单仍待补货。"],(state)=>{
      for(const [i,e] of edges.entries()){
        const item=state.get(e.key);
        const {historic,shine,text}=ink.get(e.key);
        const t=i===0?step(item.trace,0,.57):step(item.trace,.18+(i-1)*.08,.72+(i-1)*.06);
        historic.setAttribute("stroke-dashoffset",(1-t)*1000);
        historic.setAttribute("opacity",item.focus*(t===0?0:.8));
        shine.setAttribute("stroke-dashoffset",58-1058*t);
        shine.setAttribute("opacity",Math.sin(t*Math.PI)*item.focus);
        text.setAttribute("opacity",step(t,.72,1)*Math.max(.41,item.focus));
      }
    },{duration:1150,initialWait:1200,hold:2100});
}
orders();
routes();
