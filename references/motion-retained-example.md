# 成员变化：可比散点的连续追踪

此示例只覆盖同对象稳定 ID、两个范围的同轴单位与固定线性坐标可比的散点。将 `assets/chart-motion.js` 与 `assets/retained-motion.js` 按顺序各自完整内联进 HTML 的 `<script>`，再接下方片段，即为单文件；素材是合成数据。检查两轴单位、共同尺度和 ID 真实含义；不可比时不要插值，参见 [范围交替示例](motion-membership-example.md)。

保留对象从可见帧到目标连续移动，图位与数字同帧；目标摘要明确标范围，过渡值不是新观测。进入/退出用实际或当前可见坐标改变透明度，不把缺报补零。目标的坐标须均为有限数值或两者均为 null；半缺报、重复 ID 会拒绝。换数保留足够精度并核对阈值、单位、指标、导出与焦点；用户缩放、非线性尺度、不同形状和海量点须另行设计测试。控件及保留点节点复用，退出点获得焦点时示例回退目标按钮；其他可访问方式需要单独验证。

```html
<style>body{font:16px system-ui;margin:32px;color:#173239}section{max-width:860px;border:1px solid #d0dbd8;padding:20px}button{font:inherit;padding:.55em;margin-right:.5em}svg{width:100%;max-width:700px;border:1px solid #dce6e2}g:focus{outline:none}g:focus circle{stroke:#e04d26;stroke-width:3}text{font-size:11px}.status{min-height:1.5em}</style>
<h1>保留对象连续过渡实验</h1><p>数据是合成样本，两个范围分别采用同一套固定坐标；对象透明度只表示进入或退出。</p>
<section id="chart"><button data-scope="第一季">第一季</button><button data-scope="第二季">第二季</button><p class="status" role="status"></p><p class="summary"></p><p class="missing"></p>
<svg viewBox="0 0 400 230" role="group" aria-label="延迟与吞吐，横轴和纵轴均为 0 到 12"><path d="M40 15V190H370" stroke="#9cadad" fill="none"/><text x="275" y="220">延迟（ms）</text><text x="45" y="13">吞吐（单位/秒）</text><g id="marks"></g></svg></section>
<script>
const data={'第一季':[{id:'A',x:2,y:4},{id:'B',x:6,y:3},{id:'C',x:null,y:null}],'第二季':[{id:'B',x:9,y:7},{id:'C',x:null,y:null},{id:'D',x:4,y:8}]};
const host=document.getElementById('chart'), group=document.getElementById('marks'), ns='http://www.w3.org/2000/svg';let targetButton=host.querySelector('[data-scope="第一季"]');
const motion=RetainedMotion.create({scopes:data,initial:'第一季',duration:850,validate:d=>{if(d.x!==null&&(d.x<0||d.x>12||d.y<0||d.y>12))throw new RangeError('outside fixed scale')},render:f=>{
 host.querySelector('.status').textContent=f.currentValuesAreTransition?`切换中，目标 ${f.target}；图中坐标为过渡值，并非新增观测。`:`${f.target} · 已稳定`;
 host.querySelector('.summary').textContent=`目标 ${f.target}：已报 ${f.targetRecords.filter(d=>d.x!==null).length}/${f.targetRecords.length} 项`;
 host.querySelector('.missing').textContent='目标未报：'+(f.targetRecords.filter(d=>d.x===null).map(d=>d.id).join('、')||'无');
 const keep=new Set();for(const m of f.marks){keep.add(m.id);let node=[...group.children].find(n=>n.dataset.id===m.id);
  if(!node){node=document.createElementNS(ns,'g');node.dataset.id=m.id;node.setAttribute('tabindex','0');const circle=document.createElementNS(ns,'circle'), label=document.createElementNS(ns,'text');circle.setAttribute('r','7');circle.setAttribute('fill','#0b7c70');node.append(circle,label);group.append(node)}
  const x=f.currentValuesAreTransition?Math.round(m.x*100)/100:m.x,y=f.currentValuesAreTransition?Math.round(m.y*100)/100:m.y;
  node.dataset.role=m.role;node.dataset.x=String(x);node.dataset.y=String(y);node.setAttribute('opacity',String(m.opacity));node.setAttribute('transform',`translate(${40+x/12*330},${190-y/12*175})`);
  const role={retained:'保留',entered:'进入',exited:'退出','earlier-exit':'此前范围退出'}[m.role],label=`${m.id} ${role} ${f.currentValuesAreTransition?'过渡':'观测'} (${x}, ${y})`;node.setAttribute('aria-label',label);node.lastChild.setAttribute('x','10');node.lastChild.setAttribute('y','-7');node.lastChild.textContent=label;
 }
 for(const node of [...group.children])if(!keep.has(node.dataset.id)){if(document.activeElement===node)targetButton.focus({preventScroll:true});node.remove()}
}});
for(const b of host.querySelectorAll('button'))b.addEventListener('click',()=>{targetButton=b;for(const other of host.querySelectorAll('button'))other.setAttribute('aria-pressed',String(other===b));motion.set(b.dataset.scope)});
targetButton.setAttribute('aria-pressed','true');window.demoMotion=motion;
</script>
```

过渡中、快速反向、初始和运行中减少动态、键盘焦点及稳定导出均须对最终页面实测。以 motion 为实例，调用 `实例.withStableFrame(() => { /* 同步读取目标状态并导出 */ })`，退出时调用 `实例.destroy()`。示例本身不保证其他作品通过验证。
