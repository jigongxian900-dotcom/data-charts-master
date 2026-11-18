"use strict";
const model=JSON.parse(document.getElementById("model").textContent);
const observations=model.observations||[];
const nodesById=new Map(model.nodes.map(n=>[n.id,n]));
const svgNS="http://www.w3.org/2000/svg";
const reduced=matchMedia("(prefers-reduced-motion: reduce)");
const $=id=>document.getElementById(id);
const formats={
  editorial:{paper:"#f7f7f8",node:"#ffffff",ink:"#24242b",muted:"#53545d",rule:"#676873",light:"#dadbe1",accent:"#963447",focus:"#f2e4e8",band:"#f1f1f3",radius:0,serif:true},
  review:{paper:"#f3f7fa",node:"#ffffff",ink:"#172d40",muted:"#4a5e6d",rule:"#576d7f",light:"#cbd6df",accent:"#1c6284",focus:"#dcebf3",band:"#eaf1f6",radius:4,serif:false},
  projection:{paper:"#1e2025",node:"#2b2e35",ink:"#fcf3e4",muted:"#d0cad1",rule:"#b0a7b2",light:"#454650",accent:"#ffc38a",focus:"#44362d",band:"#262830",radius:1,serif:false}
};
const unit=model.unit||"";
const numeric=new Intl.NumberFormat("zh-CN");
const quantity=n=>numeric.format(n)+" "+unit;
const width=144,height=62;
const stageCount=1+Math.max(...model.nodes.map(n=>n.stage));
let layer="rules",engine,svg;
function add(parent,name,attributes,text){
  const elem=document.createElementNS(svgNS,name);
  for(const [key,value] of Object.entries(attributes))elem.setAttribute(key,value);
  if(text!==undefined)elem.textContent=text;
  parent.append(elem);return elem;
}
function txt(parent,x,y,text,fill,settings={}){
  return add(parent,"text",{x,y,fill,...settings},text);
}
function wrapLabel(label,size){
  const chars=Array.from(label);
  return Array.from({length:Math.ceil(chars.length/size)},(_,i)=>chars.slice(i*size,(i+1)*size).join(""));
}
function setTextList(id,values){
  for(const value of values){
    const row=document.createElement("li");row.textContent=value;$(id).append(row);
  }
}
function linkKey(a,b){return a+":"+b;}
const routeData=observations.map(item=>({
  ...item, byEdge:new Set(item.nodes.slice(1).map((id,i)=>linkKey(item.nodes[i],id)))
}));
const coverage=items=>items.reduce((sum,path)=>sum+path.count,0);
const summaries={
  rules:"线和节点表示流程规则。端点、分支条件和负责人可逐项核对。",
  data:"已记录 "+quantity(coverage(routeData))+"。结案 "+quantity(coverage(routeData.filter(p=>p.state==="closed")))+
       "，未结 "+quantity(coverage(routeData.filter(p=>p.state==="open")))+"。同一申请反复经过同一条边，边上只计一笔。",
};
if(model.focus_node){
  const scoped=routeData.filter(p=>p.nodes.includes(model.focus_node));
  summaries.focus="实际经过「"+nodesById.get(model.focus_node).label+"」的申请有 "+quantity(coverage(scoped))+
    "，其中结案 "+quantity(coverage(scoped.filter(p=>p.state==="closed")))+"、未结 "+
    quantity(coverage(scoped.filter(p=>p.state==="open")))+"。未结路径停在最后已知节点。";
}
$("purpose").textContent=model.purpose;
$("source").textContent=(model.period?model.period+"。":"")+model.source;
setTextList("rules",model.edges.map(edge=>{
  const a=nodesById.get(edge.from),b=nodesById.get(edge.to);
  return a.label+"（"+a.role+"） → "+b.label+"（"+b.role+"）"+(edge.label?" · "+edge.label:"");
}));
$("ledger").hidden=routeData.length===0;
setTextList("records",routeData.map(p=>p.nodes.map(id=>nodesById.get(id).label).join(" → ")+
  " · "+quantity(p.count)+" · "+(p.state==="closed"?"已结":"未结")));
const menu=[["rules","读流程规则"]];
if(routeData.length){
  menu.push(["data","叠加实际路径"]);
  if(model.focus_node)menu.push(["focus","追踪「"+nodesById.get(model.focus_node).label+"」"]);
}
const controls=menu.map(([id,label])=>{
  const button=document.createElement("button");button.type="button";button.textContent=label;
  button.addEventListener("click",()=>{if(layer!==id){layer=id;updateLayer(true);}});
  $("modes").append(button);return {id,button};
});
function position(lanes){
  const left=lanes?165:106;
  const stepX=196,stepY=105;
  const last=lanes?model.roles.length-1:Math.max(...model.nodes.map(n=>n.track));
  const graphWidth=left+(stageCount-1)*stepX+106;
  const graphHeight=134+last*stepY;
  const loc=new Map(model.nodes.map(n=>[n.id,{
    x:left+n.stage*stepX,y:65+(lanes?model.roles.indexOf(n.role):n.track)*stepY
  }]));
  return {left,stepY,graphWidth,graphHeight,loc};
}
function connection(a,b,actualIndex,pairedReturn){
  const same=a.x===b.x,forward=b.x>a.x;
  if(same){
    const sign=b.y>a.y?1:-1;
    const offset=actualIndex%2===0?-16:16;
    const xx=a.x+offset,ya=a.y+sign*height/2,yb=b.y-sign*(height/2+3);
    return {d:"M"+xx+" "+ya+" V"+yb,x:xx+8,y:(ya+yb)/2-3,
      anchor:"start",nx:xx-8,ny:(ya+yb)/2+15,na:"end"};
  }
  const sign=forward?1:-1;
  const x0=a.x+sign*width/2,x1=b.x-sign*(width/2+3);
  const delta=forward?15:-27;
  const sameTrack=Math.abs(a.y-b.y)<1;
  const reverseOffset=forward?0:16;
  const y0=a.y+reverseOffset,y1=b.y+reverseOffset;
  if(sameTrack){
    const near=(x0+x1)/2;
    const side=forward?-1:1;
    return {d:"M"+x0+" "+y0+" H"+x1,x:near,y:y0+side*11,
      anchor:"middle",nx:near,ny:y0+side*27,na:"middle"};
  }
  const mid=forward?x0+(x1-x0)*.46-7:x0+(x1-x0)*.42+9;
  const center=(y0+y1)/2;
  if(pairedReturn){
    const labelX=mid+(forward?-10:10);
    const anchor=forward?"end":"start";
    return {d:"M"+x0+" "+y0+" H"+mid+" V"+y1+" H"+x1,x:labelX,y:center-(forward?4:13),
      anchor,nx:labelX,ny:center+(forward?13:4),na:anchor};
  }
  const offset=mid+delta;
  return {d:"M"+x0+" "+y0+" H"+mid+" V"+y1+" H"+x1,x:offset,y:center-(forward?7:27),
    anchor:forward?"start":"end",nx:offset,ny:center+(forward?13:-10),na:forward?"start":"end"};
}
function nodeShape(parent,item,p,colors){
  const {x,y}=p,h=height/2,w=width/2;
  const target=item.id===model.focus_node;
  const frame={fill:target?colors.focus:colors.node,stroke:target?colors.accent:colors.rule,"stroke-width":target?1.8:1.2};
  const g=add(parent,"g",{"data-node":item.id});
  add(g,"title",{},item.label+" · "+item.role);
  if(item.kind==="decision"){
    const cut=14;
    const points=[[x-w+cut,y-h],[x+w-cut,y-h],[x+w,y],[x+w-cut,y+h],[x-w+cut,y+h],[x-w,y]];
    add(g,"polygon",{points:points.map(pair=>pair.join(",")).join(" "),...frame});
  }else add(g,"rect",{x:x-w,y:y-h,width,height,rx:item.kind==="action"?colors.radius:16,...frame});
  const label=wrapLabel(item.label,9);
  label.forEach((line,i)=>txt(g,x,y-(label.length-1)*8+i*17-2,line,colors.ink,{
    "font-size":14,"font-weight":700,"text-anchor":"middle"}));
  txt(g,x,y+(label.length===1?17:23),item.role,colors.muted,{"font-size":11,"text-anchor":"middle"});
}
function observedLayer(){
  const items=layer==="focus"?routeData.filter(p=>p.nodes.includes(model.focus_node)):routeData;
  return new Map(model.edges.map(e=>{
    const key=linkKey(e.from,e.to);
    return [key,coverage(items.filter(p=>p.byEdge.has(key)))];
  }));
}
let renderEdges,paths;
function draw(){
  engine?.destroy();
  const lanes=$("layout").value==="lanes";
  const colors=formats[$("style").value];
  const {graphWidth,graphHeight,stepY,loc}=position(lanes);
  $("canvas").replaceChildren();
  svg=add($("canvas"),"svg",{viewBox:"0 0 "+graphWidth+" "+graphHeight,role:"img",
    "aria-labelledby":"svg-title svg-description","font-family":colors.serif?"SimSun, Georgia, serif":"Microsoft YaHei, sans-serif"});
  add(svg,"title",{id:"svg-title"},model.title);
  add(svg,"desc",{id:"svg-description"},summaries[layer]+" "+model.source);
  add(svg,"rect",{x:0,y:0,width:graphWidth,height:graphHeight,fill:colors.paper});
  if(lanes)for(const [i,role] of model.roles.entries()){
    const y=13+i*stepY;
    if(i%2===0)add(svg,"rect",{x:0,y,width:graphWidth,height:stepY,fill:colors.band});
    add(svg,"line",{x1:0,y1:y+stepY,x2:graphWidth,y2:y+stepY,stroke:colors.light});
    wrapLabel(role,7).forEach((line,j)=>txt(svg,14,y+45+j*17,line,colors.muted,{"font-size":13,"font-weight":700}));
  }
  const defs=add(svg,"defs",{});
  const arrow=add(defs,"marker",{id:"wf-arrow",viewBox:"0 0 10 10",refX:8.7,refY:5,
    markerWidth:8,markerHeight:8,orient:"auto",markerUnits:"userSpaceOnUse"});
  add(arrow,"path",{d:"M0 0 L10 5 L0 10 z",fill:colors.rule});
  const declared=new Set(model.edges.map(e=>linkKey(e.from,e.to)));
  paths=model.edges.map((e,i)=>({...e,i,geo:connection(loc.get(e.from),loc.get(e.to),i,
    declared.has(linkKey(e.to,e.from)))}));
  for(const e of paths)add(svg,"path",{d:e.geo.d,fill:"none",stroke:colors.rule,"stroke-width":1.25,"marker-end":"url(#wf-arrow)"});
  renderEdges=new Map();
  for(const e of paths){
    const g=e.geo,id=linkKey(e.from,e.to);
    const trace=add(svg,"path",{d:g.d,fill:"none",stroke:colors.accent,"stroke-width":2.8,pathLength:1000,
      "stroke-linecap":"round","stroke-dasharray":"1000 1000","data-link":id});
    const chipStyle={stroke:colors.paper,"stroke-width":5,"paint-order":"stroke",
      "font-family":"Microsoft YaHei, sans-serif","stroke-linejoin":"round"};
    const text=txt(svg,g.nx,g.ny,"",colors.accent,{"font-size":12,"font-weight":700,"text-anchor":g.na,...chipStyle});
    if(e.label)txt(svg,g.x,g.y,e.label,colors.ink,{"font-size":12,"text-anchor":g.anchor,...chipStyle});
    renderEdges.set(id,{trace,text,i:e.i});
  }
  for(const n of model.nodes)nodeShape(svg,n,loc.get(n.id),colors);
  const scene=Object.fromEntries(paths.map(e=>[linkKey(e.from,e.to),{p:0,alpha:0,readout:0}]));
  engine=ChartMotion.create({scene,duration:910,paint(current,info){
    const busy=info.phase==="start"||info.phase==="transition";
    svg.dataset.phase=info.phase;
    for(const [id,geo] of current){
      const item=renderEdges.get(id);
      const shift=Math.min(.32,item.i*.045);
      const progress=Math.max(0,Math.min(1,(geo.p-shift)/(.96-shift)));
      item.trace.setAttribute("stroke-dashoffset",1000*(1-progress));item.trace.setAttribute("opacity",geo.alpha);
      item.text.setAttribute("opacity",busy?"0":geo.readout);
    }
  }});
  updateLayer(false);
}
function updateLayer(animated){
  const counts=observedLayer();
  const target={};
  for(const [id,item] of renderEdges){
    const count=counts.get(id);
    item.text.textContent=quantity(count);
    const active=layer!=="rules"&&count>0;
    target[id]={p:active?1:0,alpha:active?1:0,readout:layer==="rules"?0:count>0?1:.65};
  }
  controls.forEach(({id,button})=>button.setAttribute("aria-pressed",String(layer===id)));
  $("status").textContent=summaries[layer];
  $("guide").textContent=layer==="rules"?(routeData.length?"选择“叠加实际路径”核对发生过的申请。":"按规则图核对职责和分支。"):
    "箭头方向属于规则。强调线显示已有记录。数字为当前范围内经过该边的申请数。";
  const desc=svg.querySelector("desc");desc.textContent=summaries[layer]+" "+model.source;
  engine.to(target,{duration:animated&&!reduced.matches?910:0,meta:layer});
}
for(const id of ["layout","style"])$(id).addEventListener("change",draw);
$("export").addEventListener("click",()=>{
  const serialized=engine.withStableFrame(()=>{
    const node=svg.cloneNode(true);
    node.removeAttribute("data-phase");
    const [, , width, height]=node.getAttribute("viewBox").split(" ");
    node.setAttribute("width",width);node.setAttribute("height",height);
    return new XMLSerializer().serializeToString(node);
  });
  const url=URL.createObjectURL(new Blob([serialized],{type:"image/svg+xml"}));
  const link=document.createElement("a");link.href=url;
  link.download="workflow-"+$("layout").value+"-"+$("style").value+".svg";
  link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
draw();
