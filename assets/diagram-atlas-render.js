// All painters draw the final SVG first and register only meaningful intermediate states.
const diagramMotion = {
  graph:'沿真实连线展开', sequence:'依次呈现消息', board:'按阅读顺序显现',
  delta:'对齐变更前后', stack:'按层级展开', tables:'先识别对象，再连关系',
  iso:'沿装配轴分离或展出空间', rail:'沿有序时间轴展开', gantt:'从实际起点铺开区间',
  matrix:'按行揭示证据', scatter:'保留尺度，呈现观测', sets:'先成员集合，再显交集',
  loop:'顺相邻关系走完一轮', fishbone:'从原因分组汇入结果', route:'沿原路线逐站推进',
  orbit:'从中心展开关联', bars:'从真实零点展开', line:'沿观测顺序描线',
  radial:'在固定轴上展开量值', waterfall:'逐段核对增减', tiles:'按真实面积显现',
  heat:'固定网格，显现读数', units:'按真实单位计入', sankey:'沿真实宽度展开流向',
  'series-variant':'固定参照，逐组展开', 'sample-distribution':'固定值轴，显现样本分布','arc-network':'按依赖对象展开弧线'
};
const ns = 'http://www.w3.org/2000/svg';
const clamp = value => Math.min(1, Math.max(0, value));

function buildDiagram(host, entry) {
  host.replaceChildren();
  const jobs = [];
  const add = (tag, attrs = {}, content, parent = host) => {
    const el = document.createElementNS(ns, tag);
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
    if (content !== undefined) el.textContent = content;
    parent.append(el);
    return el;
  };
  add('title', {}, entry.title + ' · ' + entry.claim);
  add('desc', {}, entry.input);
  const defs = add('defs');
  const arrow = add('marker',{id:'arrow',viewBox:'0 0 8 8',refX:7,refY:4,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'},undefined,defs);
  add('path',{d:'M0 0L8 4L0 8Z',fill:'context-stroke'},undefined,arrow);
  const register = (el, mode, start, end, update) => {
    el.dataset.animated = mode;
    jobs.push(progress => update(clamp((progress - start) / (end - start))));
    return el;
  };
  const fade = (el, start=.1, end=.6) => register(el,'opacity',start,end,p => el.setAttribute('opacity', p));
  const slide = (el,start,end,dx,dy) => register(el,'translate',start,end,p => el.setAttribute('transform', `translate(${dx*(1-p)} ${dy*(1-p)})`));
  const path = (d, cls='wire', parent=host) => add('path',{d,class:cls},undefined,parent);
  const line = (x,y,x2,y2,cls='hair',parent=host) => add('line',{x1:x,y1:y,x2,y2,class:cls},undefined,parent);
  const rect = (x,y,w,h,cls='panel',parent=host) => add('rect',{x,y,width:w,height:h,rx:4,class:cls},undefined,parent);
  const dot = (x,y,r=5,cls='ink-dot',parent=host) => add('circle',{cx:x,cy:y,r,class:cls},undefined,parent);
  const label = (x,y,value,cls='',anchor='middle',parent=host) =>
    add('text',{x,y,class:cls,'text-anchor':anchor,'dominant-baseline':'central'},value,parent);
  const group = (parent=host) => add('g',{},undefined,parent);
  const textBlock = (x,y,value,parent=host) => {
    const parts = value.split('|');
    parts.forEach((text,index) => label(x,y+(index-(parts.length-1)/2)*18,text,index?'small muted':'strong','middle',parent));
  };
  const trace = (d, start, end, opts={}) => {
    const el=path(d,opts.cls || 'wire',opts.parent);
    const len=el.getTotalLength();
    if (opts.arrow) el.setAttribute('marker-end','url(#arrow)');
    return register(el,'dash-or-clip',start,end,p => {
      el.setAttribute('opacity', p>0 ? 1 : 0);
      if (p>=1) {
        el.removeAttribute('stroke-dashoffset');
        if (opts.dashed) el.setAttribute('stroke-dasharray','5 4');
        else el.removeAttribute('stroke-dasharray');
      } else {
        el.setAttribute('stroke-dasharray',`${len} ${len}`);
        el.setAttribute('stroke-dashoffset',len*(1-p));
      }
      if (opts.arrow) {
        if (p>=1) el.setAttribute('marker-end','url(#arrow)');
        else el.removeAttribute('marker-end');
      }
    });
  };
  const width = (el,target,start,end) => register(el,'width',start,end,p => el.setAttribute('width',target*p));
  const clip = (el,x,w,start,end) => {
    const id = 'show-' + jobs.length;
    const clipper=add('clipPath',{id},undefined,defs);
    const window=add('rect',{x,y:0,width:w,height:430},undefined,clipper);
    el.setAttribute('clip-path',`url(#${id})`);
    width(window,w,start,end);
  };
  const figure = {add,group,path,line,rect,dot,label,textBlock,fade,slide,trace,width,clip};
  painters[entry.kind](figure,entry.model);
  return progress => jobs.forEach(update => update(progress));
}

const painters = {};
painters.graph = (f,m) => {
  const {rect,label,textBlock,trace,fade,path,group,line,dot}=f;
  if (m.lanes) m.lanes.forEach((name,i)=>{
    rect(30,48+106*i,780,97,i%2?'panel':'soft');
    label(48,70+106*i,name,'small muted','start');
  });
  if (m.frame) {
    const from = m.nodes.some(n=>n[3]==='reaction') ? 32 : 224;
    rect(from,53,(m.nodes.some(n=>n[0]===3)?810:690)-from,302,'boundary');
    label(from+19,76,m.frame,'small muted','start');
  }
  const x = slot => 108+205*slot;
  const y = slot => (m.lanes?108:110)+101*slot;
  const size = node => node[3]==='reaction' ? [16,16] : node[3]==='gate' ? [56,37] : node[3]==='logic' ? [30,19] : [64,24];
  const outgoing = m.edges.map(([s])=>s);
  const earliest = new Map();
  m.edges.forEach(([a,b],i)=>{
    if(!earliest.has(a)) earliest.set(a,m.edges.some(([s,t])=>t===a && s!==b) ? .05+i*.06 : .03);
    if(!earliest.has(b)) earliest.set(b,.2+i*.067);
  });
  m.edges.forEach(([a,b,note,style],i)=>{
    const source=m.nodes[a],target=m.nodes[b];
    const start=.08+i*.63/m.edges.length;
    const ax=x(source[0]),ay=y(source[1]),bx=x(target[0]),by=y(target[1]);
    const vertical=m.levels||Math.abs(ax-bx)<40;
    const sx=Math.sign(bx-ax),sy=Math.sign(by-ay);
    const xp=vertical?ax:ax+sx*size(source)[0];
    const xq=vertical?bx:bx-sx*(size(target)[0]+3);
    const yp=vertical?ay+sy*size(source)[1]:ay;
    const yq=vertical?by-sy*(size(target)[1]+3):by;
    let d= vertical ? `M${xp},${yp} V${(yp+yq)/2} H${xq} V${yq}`
      : `M${xp},${yp} C${(xp+xq)/2},${yp} ${(xp+xq)/2},${yq} ${xq},${yq}`;
    if(style==='dashed' && sx<0) d=`M${xp},${yp} Q${xp-36},${yp+58} ${xq+26},${yq+43} T${xq},${yq}`;
    if(style==='return') d=`M${ax},${ay+24} C${ax},${ay+65} ${bx},${ay+65} ${bx},${by+28}`;
    const secondary=style==='dashed'||style==='return';
    trace(d,start,start+.24,{arrow:!m.undirected && style!=='plain',dashed:secondary,cls:secondary?'wire accent-stroke':'wire'});
    if(note) fade(label((ax+bx)/2,style==='return'?ay+29:(ay+by)/2+(style==='dashed'?48:-13),note,'small halo'),start+.13,start+.29);
  });
  m.nodes.forEach((node,i)=>{
    const [col,row,name,role]=node, ax=x(col),ay=y(row),[w,h]=size(node),g=group();
    if(role==='gate') path(`M${ax-w},${ay} L${ax},${ay-h} L${ax+w},${ay} L${ax},${ay+h}Z`,'decision',g);
    else if(role==='ellipse') f.add('ellipse',{cx:ax,cy:ay,rx:w,ry:h,class:'panel'},undefined,g);
    else if(role==='logic') {
      if(name==='AND') path(`M${ax-30},${ay+18}V${ay}A30,20 0 0 1 ${ax+30},${ay}V${ay+18}Z`,'decision',g);
      else path(`M${ax-30},${ay+19}Q${ax-24},${ay-6} ${ax},${ay-20}Q${ax+24},${ay-6} ${ax+30},${ay+19}Q${ax},${ay+6} ${ax-30},${ay+19}Z`,'decision',g);
    }
    else if(role==='actor'){
      dot(ax,ay-24,6,'ink-dot',g);
      line(ax,ay-16,ax,ay+1,'wire',g);
      line(ax-11,ay-10,ax+11,ay-10,'wire',g);
      line(ax,ay+1,ax-8,ay+12,'wire',g);
      line(ax,ay+1,ax+8,ay+12,'wire',g);
    } else {
      rect(ax-w,ay-h,2*w,2*h,role==='legacy'?'legacy':i===0?'focus-panel':'panel',g);
      if(role==='store') line(ax-w,ay-h+9,ax+w,ay-h+9,'hair',g);
    }
    textBlock(ax,ay+(role==='actor'?23:role==='reaction'?-30:0),name,g);
    const t=earliest.get(i) ?? (outgoing.includes(i)?0:.15);
    fade(g,t,Math.min(.97,t+.22));
  });
};

painters.sequence = (f,m) => {
  const x=i=>113+i*(614/(m.actors.length-1));
  m.actors.forEach((name,i)=>{
    f.rect(x(i)-67,46,134,37,'panel');
    f.label(x(i),64,name,'strong');
    f.line(x(i),84,x(i),369,'lifeline');
  });
  m.messages.forEach(([from,to,name,style],i)=>{
    const y=118+i*43,start=.045+i*.7/m.messages.length;
    const sign=Math.sign(to-from);
    f.trace(`M${x(from)},${y}H${x(to)-4*sign}`,start,start+.17,{arrow:true,dashed:style==='dashed',cls:style==='dashed'?'wire accent-stroke':'wire'});
    f.fade(f.label((x(from)+x(to))/2,y-11,name,'small halo'),start+.055,start+.21);
  });
};

painters.board = (f,m) => {
  const colWidth=218, rowHeight=m.rows.length===1?100:75;
  m.cols.forEach((name,i)=>f.label(190+i*colWidth,68,name,'strong','start'));
  m.rows.forEach(([name,...cells],r)=>{
    const y=95+r*rowHeight;
    f.label(38,y+rowHeight/2,name,'small muted','start');
    if(m.variant==='blueprint'&&r===2){
      f.line(38,y,800,y,'lifeline');
      f.label(46,y-10,'可见边界','small halo','start');
    }
    cells.forEach((value,c)=>{
      const g=f.group(), x=174+c*colWidth, t=.06+.14*c+.11*r;
      f.rect(x,y+9,colWidth-13,rowHeight-18,m.variant==='event'&&r===1?'focus-panel':'panel',g);
      f.label(x+15,y+rowHeight/2,value,(m.variant==='journey'&&r===1&&c===1?'accent-text ':'')+'small','start',g);
      f.fade(g,t,t+.25);
    });
  });
};

painters.delta = (f,m) => {
  ['变更前','变更后'].forEach((title,row)=>{
    const y=83+row*167,start=row*.39;
    f.label(77,y+20,title,'small muted','start');
    const names=row?m.after:m.before;
    const positions=row?[197,422,647]:[197,647];
    names.forEach((name,i)=>{
      const x=positions[i],g=f.group();
      f.rect(x-58,y+47,116,45,i===1&&row?'focus-panel':'panel',g);
      f.label(x,y+69,name,'strong','middle',g);
      f.fade(g,start+.03+i*.09,start+.22+i*.09);
      if(i) f.trace(`M${positions[i-1]+59},${y+69}H${x-63}`,start+.11+i*.09,start+.29+i*.09,{arrow:true});
    });
  });
  f.line(77,219,767,219);
  f.fade(f.label(422,219,m.change,'small halo accent-text'),.44,.7);
};

painters.stack = (f,m) => {
  if(m.nested){
    m.items.forEach(([title,detail],i)=>{
      const x=84+i*116,y=51+i*49,w=672-i*204,h=292-i*87,g=f.group();
      f.rect(x,y,w,h,i===2?'focus-panel':'boundary',g);
      f.label(x+16,y+24,title,'strong','start',g);
      f.label(x+16,y+44,detail,'small muted','start',g);
      f.fade(g,.06+i*.17,.33+i*.17);
    });
    return;
  }
  m.items.forEach(([title,detail],i)=>{
    const g=f.group(),y=71+i*92,w=m.pyramid?178+i*153:510;
    f.rect(420-w/2,y,w,64,(m.pipe&&i===2)||m.pyramid&&i===0?'focus-panel':'panel',g);
    f.label(m.pyramid?420:263,y+21,title,'strong','middle',g);
    f.label(m.pyramid?420:530,y+(m.pyramid?43:32),detail,'small muted','middle',g);
    f.fade(g,.055+i*.21,.3+i*.21);
    if(m.pipe&&i<2) f.trace(`M420,${y+65}v22`,.18+i*.21,.37+i*.21,{arrow:true});
  });
};

painters.tables = (f,m) => {
  const xs=m.tables.length===3?[144,420,696]:[241,610];
  m.tables.forEach(([name,...fields],i)=>{
    const x=xs[i],g=f.group();
    f.rect(x-92,121,184,139,'panel',g);
    f.rect(x-92,121,184,38,'soft',g);
    f.label(x,141,name,'strong','middle',g);
    fields.forEach((field,r)=>f.label(x-75,180+r*28,field,'small','start',g));
    f.fade(g,.04+.1*i,.38+.1*i);
    if(i){
      const left=xs[i-1]+94,right=x-96,y=m.keys?209:226,t=.4+(i-1)*.16;
      f.trace(`M${left},${y}H${right}`,t,t+.25,{arrow:!!m.classModel,dashed:!!m.classModel});
      f.fade(f.label((left+right)/2,y-15,m.rel[i-1],'small halo'),t+.08,t+.34);
    }
  });
};

painters.iso = (f,m) => {
  const project=(x,y,z)=>[364+(x-y)*1.85,232+(x+y)*.84-z];
  const polygon=(coords,style,g)=>f.add('polygon',{points:coords.map(p=>project(...p).join(',')).join(' '),class:style},undefined,g);
  const block=(x,y,z,w,d,h,i,caption)=>{
    const g=f.group();
    polygon([[x,y+d,z],[x+w,y+d,z],[x+w,y+d,z+h],[x,y+d,z+h]],'iso-front',g);
    polygon([[x+w,y,z],[x+w,y+d,z],[x+w,y+d,z+h],[x+w,y,z+h]],'iso-side',g);
    polygon([[x,y,z+h],[x+w,y,z+h],[x+w,y+d,z+h],[x,y+d,z+h]],`iso-top tone-${i}`,g);
    const [ax,ay]=project(x+w/2,y+d/2,z+h);
    f.label(ax,ay,caption,'strong halo','middle',g);
    return g;
  };
  if(m.plan){
    block(-62,-55,0,159,111,9,0,'');
    m.items.forEach((name,i)=>f.fade(block(-56+i*51,-48,9,49,90,[20,31,16][i],i,name),.08+i*.18,.38+i*.18));
  } else {
    block(-40,-26,0,89,47,17,0,m.items[2]);
    f.slide(block(-40,-26,77,89,47,12,1,m.items[1]),.12,.79,0,55);
    f.slide(block(-40,-26,150,89,47,16,2,m.items[0]),.04,.85,0,112);
  }
};

painters.rail = (f,m) => {
  const bands=m.fold?[0,m.fold]:[0];
  const span=m.fold||m.max;
  bands.forEach((from,i)=>{
    const y=bands.length===1?208:132+i*146,x=d=>103+(d-from)*640/span;
    f.line(103,y,743,y);
    f.trace(`M103,${y}H743`,.07+i*.43,.52+i*.43,{arrow:!!m.ordered,cls:'wire accent-stroke'});
    const ticks=m.ordered?m.events.map(([value])=>value):Array.from({length:span+1},(_,j)=>from+j);
    ticks.forEach(tick=>{
      f.line(x(tick),y-4,x(tick),y+7);
      f.label(x(tick),y+22,tick,'small muted');
    });
    m.events.filter(([d])=>d>=from&&d<=from+span&&(!i||d>from)).forEach(([d,name])=>{
      const t=.09+i*.43+(d-from)*.34/span,g=f.group();
      f.line(x(d),y,x(d),y-41,'hair',g);
      f.dot(x(d),y,6,'accent-dot',g);
      f.label(x(d),y-57,name,'strong','middle',g);
      f.fade(g,t,t+.14);
    });
  });
  f.label(420,355,m.axis,'small muted');
};

painters.gantt = (f,m) => {
  const scale=d=>168+d*582/m.max;
  const ticks=m.day?[0,4,8,12,16,20,24]:[0,2,4,6,8,10,12,14];
  ticks.forEach(t=>{f.line(scale(t),89,scale(t),333);f.label(scale(t),351,t,'small muted');});
  m.rows.forEach(([name,start,end],i)=>{
    const y=99+i*58,t=.08+.35*start/m.max+.06*i;
    f.label(145,y+15,name,'small','end');
    if(m.day) f.rect(scale(start),y,scale(end)-scale(start),30,'interval-track');
    f.width(f.rect(scale(start),y,scale(end)-scale(start),30,`fill tone-${i}`),scale(end)-scale(start),t,t+.38);
    f.fade(f.label(scale(end)+7,y+15,`${start}–${end}`,'small halo','start'),t+.18,t+.42);
  });
  f.label(460,384,m.day?'同一日 · 小时（UTC+8）':'距项目开始 · 天','small muted');
};

painters.matrix = (f,m) => {
  m.cols.forEach((name,i)=>f.label(348+i*146,86,name,'strong'));
  m.rows.forEach(([subject,...cells],r)=>{
    const y=114+r*68,t=.04+r*.22;
    f.label(76,y+29,subject,'strong','start');
    cells.forEach((value,c)=>{
      const x=279+c*146,g=f.group(),highlight=(m.acl&&value==='读写')||['待补','未核','未覆盖'].includes(value);
      f.rect(x,y,138,55,highlight?'focus-panel':'panel',g);
      f.label(x+69,y+27,value,'small','middle',g);
      f.fade(g,t+c*.035,t+c*.035+.31);
    });
  });
};

function axes(f, xTitle, yTitle, xTicks=[], yTicks=[]) {
  f.line(123,319,762,319,'wire');
  f.line(123,319,123,65,'wire');
  f.label(450,377,xTitle,'small muted');
  f.label(123,45,yTitle,'small muted','start');
  xTicks.forEach(([p,value])=>{
    const x=123+p*639;
    f.line(x,319,x,325);
    f.label(x,340,value,'small muted');
  });
  yTicks.forEach(([p,value])=>{
    const y=319-p*254;
    f.line(123,y,762,y,'hair');
    f.label(108,y,value,'small muted','end');
  });
}

painters.scatter = (f,m) => {
  const x=v=>123+639*v,y=v=>319-254*v;
  const steps=[0,.25,.5,.75,1];
  axes(f,m.x,m.y,m.qual?[]:steps.map(p=>[p,Math.round(p*(m.threshold?20:100))]),m.qual?[]:steps.map(p=>[p,p*(m.threshold?12:8)]));
  if(m.qual&&!m.links||m.threshold) {
    f.line(x(.5),65,x(.5),319,'lifeline');
    f.line(123,y(.5),762,y(.5),'lifeline');
  }
  (m.links||[]).forEach(([a,b],i)=>{
    const [u,v]=m.points[a],[j,k]=m.points[b];
    f.trace(`M${x(u)},${y(v)}L${x(j)},${y(k)}`,.38+i*.08,.72+i*.08);
  });
  m.points.forEach(([a,b,name],i)=>{
    const t=.08+i*.63/m.points.length,g=f.group();
    const r=m.bubble?2.8*Math.sqrt(m.points[i][3]):m.threshold?6:7;
    const mark=f.dot(x(a),y(b),r,i===0?'accent-dot':'ink-dot',g);
    if(m.bubble){
      mark.setAttribute('fill-opacity','.43');
      f.add('title',{},`${name} · ${m.points[i][3]} 宗`,mark);
    }
    if(name) f.label(x(a)+11,y(b)-12,name,'small halo','start',g);
    f.fade(g,t,t+.22);
  });
};

painters.sets = (f,m) => {
  if(m.tangent){
    f.fade(f.dot(393,207,133,'set-a'),.06,.42);
    f.fade(f.dot(463,207,63,'set-b'),.29,.68);
    f.fade(f.label(348,117,m.left,'strong'),.08,.46);
    f.fade(f.label(463,205,m.right,'strong'),.34,.73);
    f.fade(f.dot(526,207,5,'accent-dot'),.58,.88);
    f.fade(f.label(546,207,m.both,'small accent-text','start'),.64,.94);
    return;
  }
  f.fade(f.dot(354,208,127,'set-a'),.03,.47);
  f.fade(f.dot(486,208,127,'set-b'),.15,.56);
  [[293,146,m.left],[547,146,m.right],[293,213,m.onlyL],[547,213,m.onlyR],[420,213,m.both]].forEach(([x,y,name],i)=>
    f.fade(f.label(x,y,name,i===4?'strong accent-text':'strong'),i===4?.51:.28,i===4?.9:.65)
  );
  f.label(420,361,m.qual?'概念重叠 · 面积无数量含义':'同一门店口径 · 面积不表示成员数','small muted');
};

painters.loop = (f,m) => {
  const ellipse=(angle,r)=>[420+277*r*Math.cos(angle),205+143*r*Math.sin(angle)];
  const n=m.items.length;
  m.items.forEach((name,i)=>{
    const a=-Math.PI/2+i*2*Math.PI/n,b=a+2*Math.PI/n;
    const [x,y]=ellipse(a,1),[ax,ay]=ellipse(a+.29,1),[bx,by]=ellipse(b-.29,1);
    const t=.05+i*.69/n,g=f.group();
    f.trace(`M${ax},${ay}A277,143 0 0 1 ${bx},${by}`,t+.055,t+.28,{arrow:true,cls:i===0?'wire accent-stroke':'wire'});
    f.rect(x-65,y-22,130,44,i===0?'focus-panel':'panel',g);
    f.label(x,y,name,'strong','middle',g);
    if(m.notes) f.label(x,y+(i===2?-37:37),m.notes[i],'small halo','middle',g);
    if(m.signs) {
      const [sx,sy]=ellipse((a+b)/2,.84);
      f.label(sx,sy,m.signs[i],'strong accent-text','middle',g);
    }
    f.fade(g,t,t+.23);
  });
  f.label(420,203,m.center,'strong');
  if(m.hypothesis) f.label(420,227,'方向与极性为示例假设','small muted');
};

painters.fishbone = (f,m) => {
  m.items.forEach(([origin,detail],i)=>{
    const x=217+i*108,y=i%2?301:103, join=x+107,t=.06+i*.13;
    f.trace(`M${x},${y}L${join},207`,t,t+.22);
    f.fade(f.label(x-8,y,origin,'strong halo','end'),t,t+.24);
    f.fade(f.label(x-8,y+23,detail,'small muted halo','end'),t+.06,t+.28);
  });
  f.trace('M111,207H692',.38,.91,{arrow:true});
  f.fade(f.label(702,207,m.head,'strong accent-text','start'),.67,1);
  f.label(420,352,'待验证原因 · 支线无权重含义','small muted');
};

painters.route = (f,m) => {
  const paths={
    curve:'M108,303 C240,316 275,232 388,213 S584,179 728,94',
    wave:'M87,211 C160,70 216,70 285,211 S418,352 490,211 S624,70 752,211',
    meander:'M109,103 H585 Q701,103 701,160 T585,216 H258 Q163,216 163,272 T251,326 H723'
  };
  const spiral=Array.from({length:110},(_,i)=>{
    const t=i/109,a=1.6+t*10.6,r=9+t*141;
    return `${i?'L':'M'}${415+1.64*r*Math.cos(a)},${204+r*Math.sin(a)}`;
  }).join(' ');
  const spine=f.trace(paths[m.shape]||spiral,.04,.95,{arrow:m.shape!=='wave',cls:'wire accent-stroke'});
  const length=spine.getTotalLength();
  m.labels.forEach((text,i)=>{
    const p=(.08+i*.84/(m.labels.length-1)),{x,y}=spine.getPointAtLength(p*length);
    const g=f.group(),dy=m.shape==='spiral'?(i%2?24:-24):m.annotate?-40:(i%2?28:-24);
    f.dot(x,y,5,'accent-dot',g);
    if(m.annotate) f.line(x,y,x,y+dy+10,'hair',g);
    f.label(x,y+dy,text,'strong halo','middle',g);
    f.fade(g,.035+.9*p,Math.min(1,.19+.9*p));
  });
  f.label(421,380,'定性结构 · 距离无数值单位','small muted');
};

painters.orbit = (f,m) => {
  const base=m.arcs?[184,227]:[420,207];
  const coords=m.arcs?[[670,93],[670,205],[670,317]]:[[420,69],[656,207],[420,344],[185,207]];
  f.dot(...base,52,'focus-panel');
  f.label(...base,m.center,'strong');
  m.labels.forEach((value,i)=>{
    const [x,y]=coords[i],angle=Math.atan2(y-base[1],x-base[0]),a=base[0]+53*Math.cos(angle),b=base[1]+53*Math.sin(angle);
    const qx=x-36*Math.cos(angle),qy=y-36*Math.sin(angle),t=.07+i*.11;
    f.trace(m.arcs?`M${a},${b}Q${a+151},${qy+60} ${qx},${qy}`:`M${a},${b}L${qx},${qy}`,t,t+.38,{arrow:!!m.arcs});
    const g=f.group();
    f.dot(x,y,38,'panel',g);
    f.label(x,y,value,'strong','middle',g);
    f.fade(g,t+.23,t+.49);
  });
};

painters.bars = (f,m) => {
  const x=m.funnel?420:169, span=m.funnel?480:557;
  m.items.forEach(([name,value],i)=>{
    const w=value/m.max*span,y=73+i*62,t=.05+i*.139;
    const el=f.rect(m.funnel?x-w/2:x,y,w,36,`fill tone-${i}`);
    if(m.funnel){
      f.width(el,w,t,t+.34);
      f.clip(el,x-w/2,w,t,t+.34);
    } else f.width(el,w,t,t+.34);
    f.label(m.funnel?112:146,y+18,name,'strong','end');
    f.fade(f.label(m.funnel?x+w/2+9:x+w+10,y+18,value,'strong','start'),t+.18,t+.42);
  });
  if(!m.funnel){
    [0,.25,.5,.75,1].forEach(p=>{f.line(x+p*span,314,x+p*span,321);f.label(x+p*span,336,p*m.max,'small muted');});
    f.line(x,314,x+span,314);
  }
  f.label(440,371,m.unit,'small muted');
};

painters.line = (f,m) => {
  const x=i=>143+596*i/(m.items.length-1),y=v=>319-254*v/m.max;
  axes(f,'月份',m.unit,m.items.map(([name],i)=>[(x(i)-123)/639,name]),[0,20,40,60].map(v=>[v/m.max,v]));
  f.trace(m.items.map((row,i)=>`${i?'L':'M'}${x(i)},${y(row[1])}`).join(' '),.08,.92,{cls:'wire accent-stroke'});
  m.items.forEach(([,value],i)=>{
    const g=f.group(),t=.05+i*.18;
    f.dot(x(i),y(value),5,'accent-dot',g);
    f.label(x(i),y(value)-21,value,'small halo','middle',g);
    f.fade(g,t,t+.22);
  });
};

painters.radial = (f,m) => {
  const n=m.labels.length;
  const point=(i,v)=>[419+v*132*Math.sin(i/n*2*Math.PI),205-v*132*Math.cos(i/n*2*Math.PI)];
  [0.25,.5,.75,1].forEach(v=>{
    if(m.polar) f.dot(419,205,v*132,'radial-grid');
    else f.path(m.labels.map((_,i)=>`${i?'L':'M'}${point(i,v).join(',')}`).join(' ')+'Z','radial-grid');
  });
  m.labels.forEach((name,i)=>{
    f.line(419,205,...point(i,1));
    f.label(...point(i,1.19),name,'strong');
  });
  if(m.polar){
    m.values.forEach((v,i)=>{
      const [x,y]=point(i,v/m.max),t=.06+i*.1;
      f.trace(`M419,205L${x},${y}`,t,t+.36,{cls:'wire heavy accent-stroke'});
      f.fade(f.label(...point(i,v/m.max+.12),v,'small halo'),t+.2,t+.42);
    });
  } else {
    const d=m.values.map((v,i)=>`${i?'L':'M'}${point(i,v/m.max).join(',')}`).join(' ')+'Z';
    f.fade(f.path(d,'radar-fill'),.38,.9);
    f.trace(d,.08,.83,{cls:'wire accent-stroke'});
    m.values.forEach((v,i)=>f.fade(f.label(...point(i,v/m.max+.1),v,'small halo'),.08+i*.13,.32+i*.13));
  }
  f.label(419,374,`径向尺度 0–${m.max}${m.polar?' 宗':' 分'}`,'small muted');
};

painters.waterfall = (f,m) => {
  let current=m.base;
  const periods=[['期初',0,current],...m.items.map(([name,delta])=>{
    const start=current;
    current+=delta;
    return [name,start,current,delta];
  })];
  periods.push(['期末',0,current]);
  const y=value=>319-value*1.68,x=i=>152+i*132;
  axes(f,'',m.unit,[],[0,25,50,75,100,125,150].map(v=>[v*1.68/254,v]));
  periods.forEach(([name,start,end,delta],i)=>{
    const t=.03+i*.145,el=f.rect(x(i),Math.min(y(start),y(end)),72,Math.abs(y(start)-y(end)),delta<0?'negative':'fill tone-0');
    f.clip(el,x(i),72,t,t+.27);
    f.label(x(i)+36,343,name,'strong');
    f.fade(f.label(x(i)+36,Math.min(y(start),y(end))-12,delta===undefined?end:delta>0?`+${delta}`:delta,'strong halo'),t+.1,t+.29);
    if(i<periods.length-1) f.trace(`M${x(i)+73},${y(end)}H${x(i+1)}`,t+.13,t+.3,{dashed:true});
  });
};

painters.tiles = (f,m) => {
  if(m.columns){
    const total=m.columns.flatMap(([,values])=>values).reduce((a,b)=>a+b,0);
    let x=85;
    m.columns.forEach(([title,values],i)=>{
      const sum=values.reduce((a,b)=>a+b,0),w=670*sum/total,g=f.group(),t=.05+i*.22;
      let y=83;
      f.label(x+w/2,64,`${title} · ${sum} 宗`,'strong');
      values.forEach((value,j)=>{
        const h=223*value/sum;
        f.rect(x,y,w,h,`tile tone-${j}`,g);
        f.label(x+w/2,y+h/2,`${m.series[j]} ${value}`,'strong light-label','middle',g);
        y+=h;
      });
      f.clip(g,x,w,t,t+.45);
      x+=w;
    });
    f.label(420,351,m.unit,'small muted');
    return;
  }
  const total=m.items.reduce((sum,[,v])=>sum+v,0), full=650, [first,...other]=m.items, split=full*first[1]/total;
  const tile=(x,y,w,h,name,value,i)=>{
    const g=f.group(),t=.05+i*.16;
    f.rect(x,y,w,h,`tile tone-${i}`,g);
    f.label(x+14,y+23,`${name} · ${value}%`,'strong light-label','start',g);
    f.clip(g,x,w,t,t+.37);
  };
  tile(95,78,split,249,...first,0);
  let y=78;
  other.forEach(([name,value],i)=>{
    const h=value*249/(total-first[1]);
    tile(95+split,y,full-split,h,name,value,i+1);
    y+=h;
  });
  f.label(420,365,m.unit,'small muted');
};

painters.heat = (f,m) => {
  const max=Math.max(...m.rows.flatMap(([, ...values])=>values));
  m.cols.forEach((name,i)=>f.label(274+i*155,88,name,'strong'));
  m.rows.forEach(([name,...values],r)=>{
    f.label(174,139+r*62,name,'strong','end');
    values.forEach((value,c)=>{
      const x=203+c*155,y=112+r*62,g=f.group(),t=.045+r*.135+c*.087;
      const cell=f.rect(x,y,142,53,value===null?'missing':'heat-cell',g);
      if(value!==null) cell.style.fillOpacity=.1+.74*value/max;
      f.label(x+71,y+27,value===null?'未报':value,value/max>.72?'strong white':'strong','middle',g);
      f.fade(g,t,t+.28);
    });
  });
  f.label(420,345,`${m.unit} · 共同色阶 0–${max}`,'small muted');
};

painters.units = (f,m) => {
  let counter=0;
  m.items.forEach(([name,count],i)=>{
    f.dot(235+i*243,318,6,`fill tone-${i}`);
    f.label(252+i*243,318,`${name} · ${count}`,'strong','start');
    for(let k=0;k<count;k++,counter++){
      const x=193+counter%10*46,y=66+Math.floor(counter/10)*45,t=.03+.73*counter/50;
      f.fade(f.rect(x,y,30,30,`fill tone-${i}`),t,t+.16);
    }
  });
  f.label(419,363,m.unit,'small muted');
};

painters.sankey = (f,m) => {
  const x=216,right=619, scale=3,total=m.items.reduce((sum,[,v])=>sum+v,0);
  let sourceY=128,targetY=95;
  f.rect(x-12,sourceY,12,total*scale,'fill tone-0');
  f.label(x-20,204,`${m.source} · ${total}`,'strong','end');
  m.items.forEach(([name,value],i)=>{
    const h=value*scale,t=.05+i*.24,sy=sourceY,ty=targetY;
    const band=f.path(`M${x},${sy}C380,${sy} 439,${ty} ${right},${ty}v${h}C439,${ty+h} 380,${sy+h} ${x},${sy+h}Z`,`flow-band tone-${i}`);
    band.dataset.value=value;
    f.clip(band,x,right-x,t,t+.57);
    f.fade(f.rect(right,ty,12,h,`fill tone-${i}`),t+.33,t+.61);
    f.fade(f.label(right+20,ty+h/2,`${name} · ${value}`,'strong','start'),t+.56,t+.64);
    sourceY+=h;
    targetY+=h+42;
  });
  f.label(420,363,m.unit,'small muted');
};

painters['series-variant'] = (f,m) => {
  const ridge=m.shape==='ridge',stream=m.shape==='stream',bump=m.shape==='bump';
  const frames=m.labels.length,x=i=>151+i*529/(frames-1);
  m.labels.forEach((name,i)=>{
    f.line(x(i),74,x(i),316);
    f.label(x(i),339,name,'small muted');
  });
  const polyline = values => values.map(([a,b],i)=>`${i?'L':'M'}${a},${b}`).join(' ');
  const polygon = (top,bottom) => polyline([...top,...bottom.toReversed()])+'Z';
  if(stream){
    const totals=m.labels.map((_,i)=>m.series.reduce((sum,[,values])=>sum+values[i],0));
    const lower=totals.map(total=>191+total*2);
    m.series.forEach(([name,values],j)=>{
      const bottom=lower.map((height,i)=>[x(i),height]);
      const top=values.map((v,i)=>[x(i),lower[i]-4*v]);
      const band=f.path(polygon(top,bottom),`flow-band tone-${j}`);
      f.clip(band,151,529,.06+j*.12,.68+j*.12);
      f.label(696,(top.at(-1)[1]+bottom.at(-1)[1])/2,name,'small','start');
      top.forEach((point,i)=>lower[i]=point[1]);
    });
  } else if(ridge){
    m.series.forEach(([name,values],j)=>{
      const y=125+j*83,t=.05+j*.17;
      const top=values.map((v,i)=>[x(i),y-v*8]);
      f.label(133,y-10,name,'strong','end');
      f.path(polygon(top,[[x(0),y],[x(frames-1),y]]),`flow-band tone-${j}`);
      f.trace(polyline(top),t,t+.48);
    });
  } else {
    const y=v=>bump?24+v*75:304-v*2.42;
    const ticks=bump?[1,2,3]:[0,25,50,75,100];
    ticks.forEach(tick=>{
      f.line(151,y(tick),680,y(tick));
      f.label(134,y(tick),tick,'small muted','end');
    });
    m.series.forEach(([name,values],j)=>{
      const points=values.map((v,i)=>[x(i),y(v)]),t=.04+j*.12;
      f.trace(polyline(points),t,t+.52,{cls:j===1?'wire accent-stroke':'wire'});
      points.forEach(([a,b],i)=>f.fade(f.dot(a,b,4,j===1?'accent-dot':'ink-dot'),t+.37*i/(frames-1),t+.16+.45*i/(frames-1)));
      f.fade(f.label(694,y(values.at(-1)),`${name} · ${values.at(-1)}`,'small halo','start'),.52+j*.085,.74+j*.085);
    });
  }
  f.label(420,375,m.unit,'small muted');
};

painters['sample-distribution'] = (f,m) => {
  const x=value=>139+value*610/30;
  [0,5,10,15,20,25,30].forEach(v=>{
    f.line(x(v),71,x(v),325);
    f.label(x(v),346,v,'small muted');
  });
  m.items.forEach(([name,values],r)=>{
    const y=140+r*117,t=.08+r*.29;
    f.label(119,y,name,'strong','end');
    if(m.shape==='box'){
      const middle=values.length>>1,[low,q1,med,q3,high]=[values[0],values[1],values[middle],values.at(-2),values.at(-1)];
      const g=f.group();
      f.line(x(low),y,x(high),y,'wire',g);
      f.line(x(low),y-15,x(low),y+15,'wire',g);
      f.line(x(high),y-15,x(high),y+15,'wire',g);
      f.rect(x(q1),y-21,x(q3)-x(q1),42,'focus-panel',g);
      f.line(x(med),y-21,x(med),y+21,'wire accent-stroke',g);
      f.label(x(med),y-35,med,'strong halo','middle',g);
      f.fade(g,t,t+.39);
    } else {
      const seen=new Map();
      values.forEach((v,i)=>{
        const index=seen.get(v)||0;
        seen.set(v,index+1);
        const mark=f.dot(x(v),y+[0,-18,18][index],5,r?'accent-dot':'ink-dot');
        f.add('title',{},`${name} · ${v} 分钟`,mark);
        f.fade(mark,t+i*.037,t+i*.037+.24);
      });
    }
  });
  f.label(420,376,m.unit,'small muted');
};

painters['arc-network'] = (f,m) => {
  const x=i=>101+i*155, y=261;
  f.line(x(0),y,x(m.nodes.length-1),y);
  m.links.forEach(([from,to],i)=>{
    const half=(to-from)*77.5,t=.08+i*.17;
    f.trace(`M${x(from)},${y-8}A${half},${half*.7} 0 0 1 ${x(to)},${y-8}`,t,t+.35,
      {arrow:true,cls:i<2?'wire accent-stroke':'wire'});
  });
  m.nodes.forEach((name,i)=>{
    f.dot(x(i),y,5,i===2?'accent-dot':'ink-dot');
    f.label(x(i),y+28,name,'strong');
  });
  f.label(420,352,'弧线表示对象依赖 · 高度为布局','small muted');
};
