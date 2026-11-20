'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const assets = name => fs.readFileSync(path.join(__dirname,name),'utf8');
const sum = list => list.reduce((a,b)=>a+b,0);
const hours = [16,17,18,19,20,21,22];
const focus = 3;
const zones = [
  {name:'东岸',order:[172,255,370,520,430,293,152],late:[5,7,15,29,24,13,5],pending:9},
  {name:'西街',order:[145,220,325,430,372,235,130],late:[4,6,11,20,19,10,4],pending:4},
  {name:'北城',order:[185,266,408,580,460,316,166],late:[6,13,21,34,28,13,6],pending:3},
  {name:'南门',order:[125,180,270,370,300,196,114],late:[3,6,10,18,15,7,3],pending:5}
];
const target = .95;
const counts = hours.map((_,i)=>({order:sum(zones.map(z=>z.order[i])),late:sum(zones.map(z=>z.late[i])),unclassified:i===focus?sum(zones.map(z=>z.pending)):0}));
const snapshot=counts[focus];
const known=snapshot.order-snapshot.unclassified;
const ontime=known-snapshot.late;
const current=zones[2], challenger=zones[0];
const tie=current.late[focus]-challenger.late[focus], flip=tie+1;
const data={source:'原创模拟配送数据',hours,focus,target,zones,rule:'按已确认延迟数排优先，同数保留当前站。'};
assert.equal(flip,6);
const fmt = n => n.toLocaleString('en-US');
const pct = n => (100*n).toFixed(1)+'%';
const htm = s => String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const t=(x,y,s,cls='lab',a='start')=>'<text x="'+x+'" y="'+y+'" class="'+cls+'" text-anchor="'+a+'">'+htm(s)+'</text>';
const l=(x,y,X,Y,cls='rule')=>'<line x1="'+x+'" y1="'+y+'" x2="'+X+'" y2="'+Y+'" class="'+cls+'"/>';
const r=(x,y,w,h,cls='base')=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" class="'+cls+'"/>';
const c=(x,y,rad,cls='spot')=>'<circle cx="'+x+'" cy="'+y+'" r="'+rad+'" class="'+cls+'"/>';
const g=(body,at=0,mode='arrive',dur=.60)=>'<g class="'+mode+'" style="--delay:'+at+'s;--duration:'+dur+'s">'+body+'</g>';
const stroke=(coords,cls,at=.20,dur=1.10)=>'<path class="'+cls+' draw" pathLength="1" style="--delay:'+at+'s;--duration:'+dur+'s" d="'+coords.map(([x,y],i)=>(i?'L':'M')+x+' '+y).join(' ')+'"/>';
const svg=(label,body)=>'<svg viewBox="0 0 1600 900" role="img" aria-label="'+htm(label)+'">'+body+'</svg>';
const knownOf=z=>z.order[focus]-z.pending;
const rateOf=z=>1-z.late[focus]/knownOf(z);
const pages=[];
function put(ch,title,sub,body,opt={}){pages.push({ch,title,sub,body,...opt})}
function compare(label,rows,{max,x=415,y=375,row=94,span=990,unit='单'}){
  const shape=rows.map(([name,n],i)=>{
    const Y=y+i*row;
    return t(x-32,Y+8,name,'lab','end')+l(x,Y,x+span,Y)
      +g(r(x,Y-12,span*n/max,24,i===0?'hot':'base'),.18+i*.22,'from-left')
      +g(t(x+span*n/max+20,Y+13,n+' '+unit,i===0?'out accent':'out'),.82+i*.22);
  }).join('');
  return svg(label,shape+t(x,y+rows.length*row+7,'从 0 '+unit+' 起','small'));
}
const cover=svg('四区每小时已确认延迟数',zones.map((z,i)=>{
  const y=320+i*121,x=819;
  const points=z.late.map((n,j)=>[x+j*96,y+49-n*1.95]);
  return t(x,y-35,z.name,'small')+l(x,y+49,x+576,y+49)
    +stroke(points,i===2?'signal':'curve',.24+.18*i,1.44)
    +g(c(points[focus][0],points[focus][1],6,i===2?'spot':'dot')+
      t(points[focus][0]+14,points[focus][1]-5,z.late[focus],i===2?'small accent':'small'),1.36+.14*i);
}).join('')+t(1398,233,'每小时已确认延迟 · 单','small','end'));
put('Jee Charts / 运营案例','晚餐晚到了，<br>支援先去哪？','四个配送片区，一组机动支援。',cover,
  {class:'dark cover',subline:'模拟配送数据 · 19 页动态演示'});
put('从哪里开始','从高峰到一条改派规则','给当班调度带走一个决定。','<div class="contents">'+[
  ['01','晚高峰发生了什么？','工作量、准时率和四区分布',3],
  ['02','此刻先去哪一区？','已确认延迟、排序和回传界值',8],
  ['03','怎么执行和复核？','证据、调度顺序和复查时点',14]
].map(([n,a,b,page])=>'<button type="button" data-go="'+(page-1)+'"><span>'+n+'</span><strong>'+a+'</strong><small>'+b+'</small></button>').join('')+'</div>',{idle:true});
put('01 / 当班读数','19 时，四个数字先对齐','以 19:00–20:00 接单为同一批，待回传另列。',svg('19 时接单、已回传、确认延迟和待回传',[
  ['接单',snapshot.order,'单'],['已回传',known,'单'],['已确认延迟',snapshot.late,'单'],['待回传',snapshot.unclassified,'单']
].map(([name,n,u],i)=>{const x=86+(i%2)*744,y=326+Math.floor(i/2)*229;return t(x,y,name,'lab')+l(x,y+24,x+651,y+24)
  +g(t(x,y+137,fmt(n),'hero '+(i>1?'accent':''))+t(x+425,y+127,u,'small'),.17+i*.22)}).join('')), {note:'已回传 = 准时 + 延迟；待回传不填为零。'});
const rates=counts.map(v=>1-v.late/(v.order-v.unclassified));
const scaleRate=(v)=>725-(v-.90)*4500;
const ratePoints=rates.map((n,i)=>[176+208*i,scaleRate(n)]);
put('01 / 准时率','晚高峰跌到目标之下','准时率按已回传订单计算，目标为 95%。',svg('16 至 22 时的各小时准时率，19 时约 94.6%',l(176,scaleRate(target),1424,scaleRate(target),'target')
  +t(1430,scaleRate(target)-14,'目标 95%','small accent','end')
  +stroke(ratePoints,'curve')+rates.map((v,i)=>g(c(...ratePoints[i],i===focus?8:5,i===focus?'spot':'dot')+
    t(ratePoints[i][0],ratePoints[i][1]-23,pct(v),i===focus?'out accent':'small','middle')+
    t(ratePoints[i][0],771,hours[i]+' 时','small','middle'),.45+i*.18)).join('')), {note:'19 时仍有 21 单待回传，准时率仅反映当时已回传订单。'});
const peakOrder=Math.max(...counts.map(row=>row.order));
put('01 / 订单量','19 时也是订单最多的一小时','先确认峰值，再去找延迟集中在哪一区。',svg('接单量峰值 1900 单',counts.map(({order},i)=>{
  const X=191+i*191,H=352*order/peakOrder;
  return g(r(X,705-H,133,H,i===focus?'hot':'base'),.14+i*.095,'from-base')+
    g(t(X+66,685-H,fmt(order),i===focus?'out accent':'small','middle'),.75+i*.095)+t(X+66,758,hours[i]+' 时','small','middle');
}).join('')+l(162,705,1490,705)));
put('01 / 延迟位置','北城和东岸，是高峰时的两个焦点','每格保留确认延迟数，可对照同一时段。',svg('4 个片区 7 个时段的确认延迟数',hours.map((h,i)=>t(474+i*147,327,h+' 时','small','middle')).join('')+zones.map((z,i)=>{
  const Y=352+96*i;
  return t(364,Y+48,z.name,'lab','end')+z.late.map((n,j)=>{
    const X=412+j*147;
    return g(r(X,Y,124,73,j===focus&&i===2?'hot':'q'+Math.min(5,Math.floor(n/6)))+
      t(X+62,Y+47,n,j===focus&&i===2?'out inverse':'out','middle'),.16+i*.13+j*.055,'arrive',.34);
  }).join('');
}).join('')));
put('01 / 同口径比较','四区都以 95% 为目标','离目标的远近与延迟单量是两个读数。',svg('四区 19 时准时率相对目标的差距',
  l(992,329,992,727,'target')+t(994,305,'95% 目标','small accent','middle')+
  zones.map((z,i)=>{const y=392+i*93,val=rateOf(z),x=992+(val-target)*15600;
    return t(244,y+7,z.name,'lab')+l(415,y,1365,y)+g(l(992,y,x,y,'link')+c(x,y,9,'spot')+t(x+19,y-9,pct(val),'out accent'),.23*i+.24);
  }).join('')), {note:'各区准时率分母为本区已回传订单。'});
put('02 / 把窗口收窄','一组支援，<br>只能去一区','按已确认延迟数排支援；同数保留当前片区。',svg('后续使用已确认延迟数及待回传',t(1121,495,'19','hero mega accent','middle')+t(1121,564,'时 · 当班截面','lab','middle')),{class:'dark chapter',idle:true});
put('02 / 回传状态','未回传订单仍会改变排序','每条按单数绘制，三种状态明确区分。',svg('四区准时、延迟、未回传订单数量',zones.map((z,i)=>{
  const Y=376+i*87, late=z.late[focus], pending=z.pending,on=z.order[focus]-late-pending, X=376,k=1.69;
  return t(339,Y+6,z.name,'lab','end')+g(r(X,Y-17,on*k,34,'base')+r(X+on*k,Y-17,late*k,34,'hot')+
    r(X+(on+late)*k,Y-17,pending*k,34,'mutedbar'),.2*i+.13,'from-left')+
    t(X+z.order[focus]*k+18,Y+9,'延迟 '+late+'  ·  待回传 '+pending,'small');
}).join('')+t(375,774,'深  准时　　　　红  已确认延迟　　　　浅  待回传','small')));
put('02 / 以已确认排序','先给北城','北城已确认 34 单延迟，东岸 29 单，两者相差 5 单。',compare('四区已确认延迟数',[...zones].sort((a,b)=>b.late[focus]-a.late[focus]).map(z=>[z.name,z.late[focus]]),{max:50}));
const threshold = (extra=0)=>{
  const x=n=>243+(n-26)*72,y=530;
  const east=challenger.late[focus]+extra;
  return svg('东岸补传后支援阈值，34 单并列，35 单改派。',l(x(26),y,x(42),y)+
    [26,28,30,32,34,36,38,40,42].map(v=>l(x(v),y,x(v),y+9)+t(x(v),y+44,v,'small','middle')).join('')+
    l(x(34),y-79,x(34),y,'rule')+t(x(34),415,'北城 34 · 并列仍留北城','lab','middle')+
    l(x(35),y,x(35),y+90,'target')+t(x(35)+12,658,'东岸至少 35 单才改派','lab accent')+
    g(l(x(29),y,x(east),y,'signal')+c(x(east),y,13,'spot')+t(x(east)-8,y-36,'东岸 '+east+' 单','out accent','end'),.23,'arrive')+
    t(243,760,'刻度单位：已确认延迟单数','small'));
};
put('02 / 改派线','补 5 单并列，补 6 单改派','这条线假设北城维持 34 单。',threshold(6),{class:'dark',note:'严格超过才改派；图为补传情景。'});
put('02 / 缺报上界','只有东岸有机会超过北城','区间左端是已确认延迟，右端假设全部待回传都延迟。',svg('区间上界：东岸 38，北城 37，西街 24，南门 23',
  zones.map((z,i)=>{const y=365+i*94,x=n=>390+(n-15)*43;const a=z.late[focus],b=a+z.pending;
    return t(294,y+8,z.name,'lab','end')+g(l(x(a),y,x(b),y,'span')+c(x(a),y,7,'dot')+c(x(b),y,8,'hollow')+
      t(x(a)-18,y+8,a,'out','end')+t(x(b)+19,y+8,b,'out'),.2*i+.19);
  }).join('')+t(387,790,'● 已确认　　　　○ 上界','small')));
const states=[0,5,6,9];
const labels=states.map(n=>n<flip?'仍支援北城':'改派东岸');
put('02 / 试着换一个状态','回传多少，决定去哪','点击补传情况，按同一规则重算。','<div class="chooser case-controls">' + states.map((n,i)=>'<button type="button" data-variant="decision:s'+i+'" aria-pressed="'+(i===0)+'">补 '+n+' 单</button>').join('')+
  '</div><div id="case-graphic" class="case-graphic">'+threshold(0)+'</div><p id="case-verdict" class="case-verdict">'+labels[0]+'</p>',{note:'假定北城的确认数暂时维持 34 单。'});
put('03 / 调度落地','改派前，<br>先锁一个时间点','到期复看北城和东岸的真实回传。',svg('派工前先锁回传截点',t(1120,513,'19:15','hero mega accent','middle')+t(1120,584,'建议复核时点','lab','middle')),{class:'dark chapter',idle:true});
const chain = [['核回传','冻结两区读数'],['套规则','严格超过才改派'],['派支援','记录指令和去向'],['再复核','看超时积压是否下降']];
put('03 / 执行动作','从回传到签收，四步闭环','每一步都留下下一位能核查的对象。',svg('调度流程，同步校验、比较、派出、复核',
  chain.map(([a,b],i)=>{const x=99+i*373;
    return g(r(x,389,279,190,i===1?'hot':'light')+t(x+27,465,a,i===1?'flow inverse':'flow')+
      t(x+27,528,b,i===1?'small inverse':'small')+(i<3?t(x+298,484,'→','out accent'):''),.22+i*.34);
  }).join('')));
put('03 / 上界复核','北城再补 3 单，改派线随之移动','若北城升到 37 单，东岸必须到 38 单，对应补 9 单。',svg('北城原确认 34，补 3 后为 37，改派目标由 35 变成 38',
  l(252,515,1344,515)+g(c(484,515,10,'dot')+t(484,465,'34','hero','middle')+t(484,588,'北城当前','lab','middle'),.2)+
  g(l(484,515,884,515,'signal')+c(884,515,11,'spot')+t(884,465,'37','hero accent','middle')+t(884,588,'北城补 3','lab','middle'),.82)+
  g(c(1017.33,515,11,'spot')+t(1114,455,'38','hero accent','middle')+t(1114,590,'东岸改派线','lab','middle'),1.56)));
put('03 / 复核指标','看积压，也看支援有没有代价','试行前后使用相同时间窗与同一准时规则。','<div class="checklist">'+[
  ['准时率','分母固定为已回传订单，待回传另列。'],['延迟存量','逐区记录已确认延迟与滞留时长。'],
  ['支援成本','记录调度次数、支援工时与未处理单量。']
].map(([a,b])=>'<div><strong>'+a+'</strong><span>'+b+'</span></div>').join('')+'</div>',{idle:true});
put('03 / 当班安排','19:15 锁数，19:20 回看','负责人、反馈时点和使用同一份台账。','<div class="checklist">'+[
  ['19:10 · 区域负责人','补齐延迟状态，缺报原因单独登记。'],['19:15 · 调度岗','依确认数执行优先级，并记录是否切换。'],
  ['19:20 · 值班负责人','复核两区积压和支援工时，确认是否继续。']
].map(([a,b])=>'<div><strong>'+a+'</strong><span>'+b+'</span></div>').join('')+'</div>',{idle:true});
put('回答开场问题','先去北城。<br>补足再改派。','北城当前 34 单，东岸 29 单。北城暂不变时，东岸需补至少 6 单。',svg('结论：先北城，东岸至少补 6 单才改派。',
  t(1120,505,'+6','hero mega accent','middle')+t(1120,583,'单 · 东岸最低改派条件','lab','middle')+
  l(848,643,1420,643)+t(1132,694,'19:15 复核回传','small','middle')),{class:'dark cover',idle:true,subline:'Jee Charts · 模拟配送数据'});
assert.equal(pages.length,19);
const variant={decision:Object.fromEntries(states.map((n,i)=>['s'+i,{html:{'#case-graphic':threshold(n)},text:{'#case-verdict':labels[i]},replay:true}]))};
const css=fs.readFileSync(path.join(__dirname,'deck.css'),'utf8');
const ship='<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>晚餐晚到了 · Jee Charts</title><style>'
  +assets('presentation-stage.css')+css+'</style></head><body><main class="viewport"><div class="frame"><div class="stage" tabindex="-1">'
  +pages.map((p,i)=>'<section class="scene '+(p.class||'')+'" data-layout="'+(i+1)+'" data-label="'+htm(p.title.replace(/<br>/g,''))+'" data-motion="'+(p.idle?'idle':'evidence')+'"'+(i?' hidden':'')+'>'
  +'<header class="scene-head"><p>'+p.ch+'</p>'+(i?'<h2>':'<h1>')+p.title+(i?'</h2>':'</h1>')+'<p class="subtitle">'+p.sub+'</p></header>'
  +'<div class="graphic">'+p.body+'</div><footer><span>'+htm(p.note||p.subline||'原创模拟配送数据 · Jee Charts')+'</span><span>'+String(i+1).padStart(2,'0')+' / 19</span></footer></section>').join('')
  +'</div></div></main><p id="announcement" class="visually-hidden" aria-live="polite"></p><button class="peek" data-action="overview">总览</button>'
  +'<nav class="dockbar"><div class="dock"><button id="prev" data-action="prev" aria-label="上一页">←</button><span id="count"></span><button id="next" data-action="next" aria-label="下一页">→</button><button data-action="overview">总览</button><button data-action="replay">重播</button><button id="auto" data-action="auto">连播</button><button data-action="full">全屏</button></div></nav>'
  +'<dialog id="overview" class="tray"><header><h2>19 页总览</h2><form method="dialog"><button>关闭</button></form></header><div class="gallery"></div></dialog>'
  +'<script id="variants" type="application/json">'+JSON.stringify(variant).replaceAll('<','\\u003c')+'</script>'
  +'<script id="evidence" type="application/json">'+JSON.stringify(data)+'</script>'
  +'<script>'+assets('presentation-stage.js')+'</script></body></html>';
fs.mkdirSync(path.join(__dirname,'..','..','docs','showcase'),{recursive:true});
fs.writeFileSync(path.join(__dirname,'..','..','docs','showcase','dispatch-deck.html'),'<!doctype html>'+ship);
fs.writeFileSync(path.join(__dirname,'..','..','docs','showcase','dispatch-data.json'),JSON.stringify(data,null,2)+'\n');
