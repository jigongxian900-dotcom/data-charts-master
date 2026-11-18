"use strict";
const source=JSON.parse(document.querySelector("#source").textContent);
const NS="http://www.w3.org/2000/svg";
const reduce=matchMedia("(prefers-reduced-motion: reduce)");
const w=520,h=228;
const C=["var(--mark)","var(--mark2)","var(--mark3)","var(--mark4)"];
const signed=n=>(n>0?"+":"")+n;
const clamp=n=>Math.max(0,Math.min(1,n));
const stage=(p,start,end)=>clamp((p-start)/(end-start));
const ease=p=>1-(1-p)**3;
const lerp=(a,b,p)=>a+(b-a)*p;
const attrs=(el,values)=>{for(const [k,v] of Object.entries(values))el.setAttribute(k,v);};
function html(tag,text,cls){
  const el=document.createElement(tag);
  if(text!==undefined)el.textContent=text;
  if(cls)el.className=cls;
  return el;
}
function svgNode(parent,tag,values,text){
  const el=document.createElementNS(NS,tag);
  attrs(el,values);
  if(text!==undefined)el.textContent=text;
  parent.append(el);
  return el;
}
function label(svg,x,y,text,attribute={}){
  return svgNode(svg,"text",{x,y,...attribute},text);
}
function line(svg,x1,y1,x2,y2,cls="axis"){
  return svgNode(svg,"line",{x1,y1,x2,y2,class:cls});
}
function rect(svg,x,y,width,height,more={}){
  return svgNode(svg,"rect",{x,y,width,height,...more});
}
function dot(svg,cx,cy,r,more={}){
  return svgNode(svg,"circle",{cx,cy,r,...more});
}
function path(svg,d,more={}){
  return svgNode(svg,"path",{d,fill:"none",...more});
}
function rowAxes(svg,{x0=104,x1=485,y0=195,domain,marks}){
  const place=v=>lerp(x0,x1,(v-domain[0])/(domain[1]-domain[0]));
  for(const v of marks){
    line(svg,place(v),23,place(v),y0);
    label(svg,place(v),y0+19,String(v),{"text-anchor":"middle",class:"small"});
  }
  line(svg,x0,y0,x1,y0);
  return place;
}
function flow(svg,values){
  const yL={"线上":48,"门店":136},yR={"已交付":41,"待处理":149};
  const lx=112,rx=407,scale=1.22;
  const leftUsed={},rightUsed={};
  const ribbons=values.map(([from,to,n],i)=>{
    const s=n*scale;
    const y1=yL[from]+(leftUsed[from]||0)+s/2,y2=yR[to]+(rightUsed[to]||0)+s/2;
    leftUsed[from]=(leftUsed[from]||0)+s;
    rightUsed[to]=(rightUsed[to]||0)+s;
    const d="M"+lx+" "+y1+" C"+(lx+105)+" "+y1+" "+(rx-105)+" "+y2+" "+rx+" "+y2;
    const color=to==="已交付"?C[0]:C[1];
    const band=path(svg,d,{stroke:color,"stroke-width":s,opacity:.25});
    const flare=path(svg,d,{stroke:color,"stroke-width":Math.max(2,s*.2),
      "stroke-linecap":"round",pathLength:1000,"stroke-dasharray":"54 1300",opacity:0});
    svgNode(band,"title",{},from+" → "+to+" "+n+" 单");
    return {band,flare,i};
  });
  for(const [i,[name,y]] of Object.entries(yL).entries()){
    rect(svg,lx-6,y,5,leftUsed[name],{fill:C[0]});
    label(svg,lx-13,y+13,name,{"text-anchor":"end"});
    label(svg,lx-13,y+30,String(Math.round(leftUsed[name]/scale))+" 单",{"text-anchor":"end",class:"number"});
  }
  for(const [name,y] of Object.entries(yR)){
    rect(svg,rx+1,y,5,rightUsed[name],{fill:name==="已交付"?C[0]:C[1]});
    label(svg,rx+13,y+13,name);
    label(svg,rx+13,y+30,String(Math.round(rightUsed[name]/scale))+" 单",{class:"number"});
  }
  label(svg,lx,22,"订单入口",{class:"small"});
  label(svg,rx,22,"当前去向",{"text-anchor":"end",class:"small"});
  return p=>ribbons.forEach(({band,flare,i})=>{
    const t=stage(p,i*.055,.76+i*.055);
    band.setAttribute("opacity",lerp(.13,i%2===0?.46:.42,ease(t)));
    attrs(flare,{"stroke-dashoffset":lerp(58,-1000,t),opacity:Math.sin(t*Math.PI)**.8});
  });
}
function trend(svg,values){
  const x=i=>lerp(52,485,i/(values.length-1)),y=v=>182-v/120*149;
  for(const v of [0,40,80,120]){line(svg,52,y(v),485,y(v));label(svg,43,y(v)+4,String(v),{"text-anchor":"end",class:"small"});}
  for(const i of [0,2,4,6,7])label(svg,x(i),203,(i+1)+"月",{"text-anchor":"middle",class:"small"});
  const d=values.map((v,i)=>(i?"L":"M")+x(i)+" "+y(v)).join(" ");
  const defs=svgNode(svg,"defs",{});
  const clip=svgNode(defs,"clipPath",{id:"trend-clip"});
  const window=rect(clip,46,18,450,173);
  const marks=svgNode(svg,"g",{"clip-path":"url(#trend-clip)"});
  path(marks,d+" L485 182 H52 Z",{fill:C[0],"fill-opacity":.13});
  path(marks,d,{stroke:C[0],"stroke-width":3});
  for(const [i,v] of values.entries())dot(marks,x(i),y(v),3.5,{fill:C[0]});
  const endpoint=label(svg,485,y(values.at(-1))-12,String(values.at(-1)),{"text-anchor":"end",class:"number",opacity:0});
  const head=dot(svg,x(0),y(values[0]),5,{fill:C[1]});
  return p=>{
    const u=ease(p)*(values.length-1),i=Math.min(values.length-2,Math.floor(u));
    const xx=lerp(x(i),x(i+1),u-i),yy=lerp(y(values[i]),y(values[i+1]),u-i);
    attrs(window,{width:xx-46+6});attrs(head,{cx:xx,cy:yy,opacity:p<1?1:0});
    endpoint.setAttribute("opacity",stage(xx,x(values.length-1)-.4,x(values.length-1)));
  };
}
function ranking(svg,values){
  const x0=116,x1=429,y=r=>43+(r-1)*43;
  label(svg,x0,21,"上季",{"text-anchor":"middle",class:"small"});
  label(svg,x1,21,"本季",{"text-anchor":"middle",class:"small"});
  const tokens=values.map(([name,a,b],i)=>{
    const highlight=name==="东区",color=highlight?C[1]:C[0];
    const shape="M"+x0+" "+y(a)+" C232 "+y(a)+" 306 "+y(b)+" "+x1+" "+y(b);
    path(svg,shape,{stroke:color,"stroke-opacity":highlight?.34:.22,"stroke-width":highlight?3:2});
    label(svg,103,y(a)+4,name+" "+a,{"text-anchor":"end",class:highlight?"number":"small"});
    label(svg,444,y(b)+4,b+" "+name,{class:highlight?"number":"small"});
    const moving=path(svg,shape,{stroke:color,"stroke-width":highlight?3:2,pathLength:1000,"stroke-dasharray":"1000 1000"});
    return {moving,dot:dot(svg,x0,y(a),highlight?6:4,{fill:color}),i};
  });
  return p=>tokens.forEach(({moving,dot:point,i})=>{
    const t=ease(stage(p,i*.045,.85+i*.045));
    const loc=moving.getPointAtLength(moving.getTotalLength()*t);
    attrs(point,{cx:loc.x,cy:loc.y});
    moving.setAttribute("stroke-dashoffset",1000*(1-t));
  });
}
function waterfall(svg,values){
  const base=176,y=v=>base-v/120*144,x=i=>63+i*74;
  for(const v of [0,40,80,120]){line(svg,41,y(v),488,y(v));label(svg,35,y(v)+4,String(v),{"text-anchor":"end",class:"small"});}
  let cumulative=0;
  const bars=values.map(([name,value],i)=>{
    const total=i===0||i===values.length-1;
    const from=total?0:cumulative;
    const to=total?value:from+value;
    cumulative=to;
    const color=total?C[2]:value<0?C[1]:C[0];
    const bar=rect(svg,x(i)-18,y(from),36,0,{fill:color,rx:1});
    const readout=label(svg,x(i),Math.min(y(from),y(to))-7,total?String(value):signed(value),
      {"text-anchor":"middle",class:"number",opacity:0});
    label(svg,x(i),204,name,{"text-anchor":"middle",class:"small"});
    const connector=i<values.length-1?line(svg,x(i)+18,y(to),x(i+1)-18,y(to),"ref"):null;
    if(connector)connector.setAttribute("opacity",0);
    return {from,to,bar,readout,connector,i};
  });
  return p=>bars.forEach(({from,to,bar,readout,connector,i})=>{
    const t=ease(stage(p,i*.12,i*.12+.33)),yy=y(lerp(from,to,t)),ref=y(from);
    attrs(bar,{y:Math.min(yy,ref),height:Math.abs(yy-ref)});
    readout.setAttribute("opacity",stage(t,.72,1));
    connector?.setAttribute("opacity",stage(t,.6,1));
  });
}
function delta(svg,values){
  const x=rowAxes(svg,{domain:[-25,25],marks:[-25,-10,0,10,25]});
  const zero=x(0);
  line(svg,zero,22,zero,195,"ref");
  const bars=values.map(([name,n],i)=>{
    const yy=35+i*37,at=x(n);
    label(svg,89,yy+13,name,{"text-anchor":"end"});
    const bar=rect(svg,zero,yy,0,16,{fill:n<0?C[1]:C[0],rx:1});
    const lab=label(svg,at+(n<0?6:-6),yy+12,signed(n),{
      "text-anchor":n<0?"start":"end",fill:"var(--svg-bg)",class:"number",opacity:0});
    lab.style.fill=(Math.abs(n)>=5)?"var(--svg-bg)":"var(--label)";
    return {bar,lab,at,i};
  });
  return p=>bars.forEach(({bar,lab,at,i})=>{
    const finish=lerp(zero,at,ease(stage(p,i*.10,.63+i*.10)));
    attrs(bar,{x:Math.min(zero,finish),width:Math.abs(zero-finish)});
    lab.setAttribute("opacity",stage(p,.59+i*.09,.73+i*.09));
  });
}
function bullet(svg,values,target){
  const x=rowAxes(svg,{domain:[0,120],marks:[0,30,60,90,120]});
  const series=values.map(([name,n],i)=>{
    const yy=31+i*39;
    label(svg,91,yy+22,name,{"text-anchor":"end"});
    rect(svg,x(0),yy+6,x(120)-x(0),16,{fill:"var(--graph-rule)"});
    const bar=rect(svg,x(0),yy+9,1,10,{fill:C[0]});
    const end=dot(svg,x(0),yy+14,4.3,{fill:C[0]});
    const ref=line(svg,x(target),yy+2,x(target),yy+26,"ref");attrs(ref,{"stroke-width":2});
    const lab=label(svg,x(n)+8,yy+17,String(n),{class:"number",opacity:0});
    return {bar,end,lab,n,i};
  });
  return p=>series.forEach(({bar,end,lab,n,i})=>{
    const t=ease(stage(p,i*.09,.67+i*.09)),xEnd=x(n*t);
    attrs(bar,{width:xEnd-x(0)});attrs(end,{cx:xEnd});
    lab.setAttribute("opacity",stage(t,.73,1));
  });
}
function stack(svg,values){
  const x0=69,span=416;
  label(svg,x0,43,"上期",{class:"small"});const mode=label(svg,x0,129,"向本期过渡",{class:"small"});
  let prior=0;
  const series=values.map(([name,a,b],i)=>{
    const color=C[i],start=x0+span*prior/100;
    prior+=a;
    rect(svg,start,52,span*a/100,20,{fill:color,opacity:.35,stroke:"var(--svg-bg)","stroke-width":1});
    const band=rect(svg,start,139,span*a/100,26,{fill:color,stroke:"var(--svg-bg)","stroke-width":1});
    const title=label(svg,66+i*149,194,name+" "+a+"% → "+b+"%",{class:"small"});
    title.setAttribute("fill",color);
    return {a,b,band};
  });
  return p=>{
    let sum=0;
    for(const {a,b,band} of series){
      const portion=lerp(a,b,ease(p));
      attrs(band,{x:x0+span*sum/100,width:span*portion/100});
      sum+=portion;
    }
    mode.textContent=p===1?"本期":"过渡示意";
  };
}
function donut(svg,values){
  const cx=143,cy=111,r=65,CIRCLE=2*Math.PI*r;
  dot(svg,cx,cy,r,{fill:"none",stroke:"var(--graph-rule)","stroke-width":22});
  let sum=0;
  const parts=values.map(([name,n],i)=>{
    const arc=dot(svg,cx,cy,r,{fill:"none",stroke:C[i],"stroke-width":22,
      transform:"rotate("+(sum*3.6-90)+" "+cx+" "+cy+")","stroke-dasharray":"0 "+CIRCLE});
    const yy=55+i*37;
    rect(svg,293,yy-10,10,10,{fill:C[i]});
    label(svg,315,yy,name);label(svg,456,yy,n+"%",{"text-anchor":"end",class:"number"});
    svgNode(arc,"title",{},name+" "+n+"%");
    const start=sum;sum+=n;return {arc,start,end:sum};
  });
  const number=label(svg,cx,112,values[0][1]+"%",{"text-anchor":"middle",class:"number",opacity:0});
  number.style.fontSize="31px";label(svg,cx,134,values[0][0],{"text-anchor":"middle",class:"small"});
  return p=>{
    const at=ease(p)*100;
    for(const {arc,start,end} of parts)arc.setAttribute("stroke-dasharray",Math.max(0,Math.min(at,end)-start)/100*CIRCLE+" "+CIRCLE);
    number.setAttribute("opacity",stage(p,.52,.78));
  };
}
function treemap(svg,values){
  const x0=32,y0=27,W=456,H=163;
  const firstW=W*values[0][1]/100;
  let nextY=y0;
  const tiles=values.map(([name,n],i)=>{
    const tx=i?x0+firstW:x0,ty=i?nextY:y0;
    const tw=i?W-firstW:firstW,th=i?H*n/(100-values[0][1]):H;
    if(i)nextY+=th;
    const g=svgNode(svg,"g",{});
    rect(g,tx,ty,tw,th,{fill:C[i],opacity:i?.16:.24,stroke:C[i],"stroke-width":1.2});
    label(g,tx+11,ty+th/2+4,name);
    label(g,tx+tw-12,ty+th/2+4,n+"%",{"text-anchor":"end",class:"number"});
    return {g,tx,ty,i};
  });
  return p=>tiles.forEach(({g,tx,ty,i})=>{
    const t=ease(stage(p,i*.09,.62+i*.09)),scale=lerp(.88,1,t);
    attrs(g,{opacity:t,transform:"translate("+tx+" "+ty+") scale("+scale+") translate("+(-tx)+" "+(-ty)+")"});
  });
}
function scatter(svg,values){
  const x=rowAxes(svg,{x0:51,x1:474,y0:183,domain:[0,40],marks:[0,10,20,30,40]}),
    y=v=>183-v/70*151;
  for(const v of [0,20,40,60]){line(svg,51,y(v),474,y(v));label(svg,42,y(v)+4,String(v),{"text-anchor":"end",class:"small"});}
  line(svg,x(20),26,x(20),183,"ref");line(svg,51,y(40),474,y(40),"ref");
  label(svg,51,20,"产出",{class:"small"});label(svg,491,202,"投入",{class:"small"});
  const points=values.map(([a,b],i)=>{
    const el=dot(svg,x(a),y(b),4,{fill:b>=40?C[0]:C[1],opacity:0,stroke:"var(--svg-bg)","stroke-width":1});
    svgNode(el,"title",{},"门店 "+(i+1)+"，投入 "+a+" 万，产出 "+b+" 万");
    return el;
  });
  return p=>points.forEach((el,i)=>{
    const t=ease(stage(p,i*.027,.42+i*.027));attrs(el,{opacity:t,r:lerp(1.8,5.2,t)});
  });
}
function heat(svg,values){
  const colors=["#eeeef0","#dcdde0","#c3c6cc","#a4aab3","#565e69","#363d48"];
  const defs=svgNode(svg,"defs",{});
  const pattern=svgNode(defs,"pattern",{id:"unreported",width:5,height:5,patternUnits:"userSpaceOnUse",patternTransform:"rotate(35)"});
  svgNode(pattern,"line",{x1:0,y1:0,x2:0,y2:5,stroke:C[3],"stroke-width":1});
  const cells=[];
  for(const [i,row] of values.entries()){
    label(svg,61,53+i*29,["周一","周二","周三","周四","周五"][i],{"text-anchor":"end",class:"small"});
    for(const [j,n] of row.entries()){
      if(i===0)label(svg,103+j*67,26,[8,10,12,14,16,18][j]+"时",{"text-anchor":"middle",class:"small"});
      const tone=n===null?-1:Math.min(colors.length-1,Math.floor(n/15));
      const box=rect(svg,72+j*67,34+i*29,63,25,{fill:tone<0?"url(#unreported)":colors[tone],opacity:0});
      const text=label(svg,103+j*67,52+i*29,n===null?"未报":String(n),{"text-anchor":"middle",opacity:0});
      text.style.fill=tone>=4?"var(--svg-bg)":"#19191b";
      cells.push({box,text,j,i});
    }
  }
  return p=>cells.forEach(({box,text,j,i})=>{
    const delay=(j*5+i)*.017;
    const t=ease(stage(p,delay,delay+.40));
    box.setAttribute("opacity",t);text.setAttribute("opacity",stage(t,.53,1));
  });
}
function interval(svg,values){
  const x=rowAxes(svg,{domain:[-8,8],marks:[-8,-4,0,4,8]});
  line(svg,x(0),23,x(0),195,"ref");
  const marks=values.map(([name,n,lo,hi],i)=>{
    const yy=37+i*38,estimate=x(n),a=x(lo),b=x(hi),color=lo>0||hi<0?C[0]:C[3];
    label(svg,88,yy+4,name,{"text-anchor":"end"});
    const range=line(svg,estimate,yy,estimate,yy);attrs(range,{stroke:color,"stroke-width":2});range.style.stroke=color;
    const l=line(svg,a,yy-4,a,yy+4),r=line(svg,b,yy-4,b,yy+4);
    l.style.stroke=color;r.style.stroke=color;
    const central=dot(svg,estimate,yy,5,{fill:color,stroke:"var(--svg-bg)","stroke-width":1.2});
    svgNode(central,"title",{},name+" "+signed(n)+" 个百分点；95% CI "+lo+" 至 "+hi);
    return {range,l,r,central,a,b,estimate,i};
  });
  return p=>marks.forEach(({range,l,r,central,a,b,estimate,i})=>{
    const t=stage(p,.12+i*.08,.65+i*.08);
    central.setAttribute("opacity",stage(p,i*.06,i*.06+.16));
    attrs(range,{x1:lerp(estimate,a,ease(t)),x2:lerp(estimate,b,ease(t))});
    for(const bar of [l,r])bar.setAttribute("opacity",stage(t,.77,1));
  });
}
const chartTypes={flow,trend,ranking,waterfall,delta,bullet,stack,donut,treemap,scatter,heat,interval};
const durations={flow:1800,trend:1230,ranking:1600,waterfall:1950,delta:1330,bullet:1320,
  stack:1580,donut:1410,treemap:1200,scatter:1230,heat:1580,interval:1440};
const entries=new Map();
function mount(id,figure,featured=false){
  const item=source.cases[id];
  figure.id=featured?"hero-chart":id;
  figure.dataset.chart=id;
  const heading=html(featured?"h2":"h3",item.name);
  const svg=svgNode(figure,"svg",{viewBox:"0 0 "+w+" "+h,role:"img","aria-label":item.name,
    class:"chart",preserveAspectRatio:"xMidYMid meet"});
  figure.prepend(html("p",item.type+" · "+item.scope,"meta"),heading);
  const painter=chartTypes[id](svg,item.values,item.target);
  const caption=html("figcaption",item.caption);
  const details=html("details");
  details.append(html("summary","查看数据"),html("pre",item.values.map(value=>Array.isArray(value)?
    value.map(v=>v===null?"未报":v).join(" · "):String(value)).join("\n")));
  figure.append(caption,details);
  const state=ChartMotion.create({
    scene:{reveal:{p:reduce.matches?1:0}},
    paint(scene,info){
      const {p}=scene.get("reveal");
      painter(p);
      figure.dataset.progress=p;
      figure.dataset.phase=info.phase;
      if(p===1)figure.dataset.finished="true";
    }
  });
  entries.set(figure,state);
}
mount("flow",document.getElementById("hero-chart"),true);
const gallery=document.getElementById("gallery"),nav=document.getElementById("nav-links");
for(const group of source.groups){
  const anchor=html("a",group.name);anchor.href="#"+group.id;nav.append(anchor);
  const section=html("section",undefined,"chapter");section.id=group.id;
  const heading=html("div",undefined,"heading");heading.append(html("h2",group.name),html("p",group.intro));
  const cards=html("div",undefined,"cards");
  section.append(heading,cards);gallery.append(section);
  for(const id of group.cases){const f=html("figure",undefined,"card");cards.append(f);mount(id,f);}
}
gallery.append(html("footer","数据均为见数原创合成样例。"));
function start(figure,instant=false){
  if(figure.dataset.seen)return;
  figure.dataset.seen="true";
  entries.get(figure).to({reveal:{p:1}},{duration:instant||reduce.matches?0:durations[figure.dataset.chart],ease:p=>p});
}
if("IntersectionObserver" in window){
  const watcher=new IntersectionObserver(visits=>{
    for(const visit of visits)if(visit.isIntersecting&&visit.intersectionRatio>=.58){
      watcher.unobserve(visit.target);start(visit.target.closest("figure"));
    }
  },{threshold:[.58]});
  for(const figure of entries.keys())watcher.observe(figure.querySelector("svg"));
}else for(const figure of entries.keys())start(figure,true);
reduce.addEventListener("change",event=>{
  if(event.matches)for(const figure of entries.keys())start(figure,true);
});
window.addEventListener("beforeprint",()=>{
  for(const [figure,state] of entries){start(figure,true);state.finish();}
});
