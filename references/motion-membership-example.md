# 成员变化：旧范围和新范围分层切换

旧范围和目标范围**分别展示各自真实观测**，并标范围、摘要、分母及同量纲固定尺度；透明度仅表示切换，不代表数据。演示柱图与散点，样例数据为合成。将 `assets/chart-motion.js` 与 `assets/membership-motion.js` 按顺序完整内联到 HTML 的 `<script>`，再接下方片段。切换前应先决定是否适合交替：坐标/单位不兼容时须明确标注各范围自己的轴与单位，不能用同轴暗示可比；没有追踪价值也可即时切换。

`scopes` 是范围名至记录数组的映射，记录要求非空唯一 `id`。`validate` 由业务作者检查有限值和缺失；保留快照不可原地更改，数据刷新时销毁并重建。`render` 对每层的 `marks` 绘制其真实数据并说明 retained/entered/exited，旧范围对读屏隐藏，目标摘要明确标为目标；缺报显示未报，不补零。此示例每帧重建静态图层，仅保留外层控件节点；含可聚焦图元、大规模数据、复杂类型时需设计复用节点、焦点回退及性能验证。本示例是分层切换，不是保留对象的连续位移。

```html
<style>body{font:16px system-ui;margin:32px;color:#182b32}section{border:1px solid #cad6d5;padding:14px;margin:20px 0}button{font:inherit;padding:.5em;margin-right:.5em}.layer{border-top:1px solid #ddd;padding:6px}.layer h4,.layer p{margin:3px}svg{max-width:100%;height:100px}.warning{font-size:.9em}</style>
<h1>范围变化动效实验</h1><p>两张图均为合成数据；每个范围独立显示，透明度仅表示过渡，不代表比例或权重。</p>
<section id="bar"><h2>门店备货（件）</h2><button data-scope="东区">东区</button><button data-scope="西区">西区</button><p class="status" role="status"></p><p class="target"></p><div class="layers"></div></section>
<section id="scatter"><h2>设备压力与温度</h2><button data-scope="早班">早班</button><button data-scope="晚班">晚班</button><p class="status" role="status"></p><p class="target"></p><div class="layers"></div></section>
<script>
const barScopes={'东区':[{id:'A',v:9},{id:'B',v:7},{id:'C',v:null}],'西区':[{id:'B',v:11},{id:'C',v:null},{id:'D',v:5}]};
const scatterScopes={'早班':[{id:'L',x:3,y:6},{id:'M',x:6,y:4},{id:'N',x:null,y:null}],'晚班':[{id:'M',x:5,y:7},{id:'N',x:null,y:null},{id:'P',x:8,y:3}]};
const ns='http://www.w3.org/2000/svg';
function setup(sectionId,scopes,initial,type){
  const section=document.getElementById(sectionId), layerBox=section.querySelector('.layers');
  const valid=d=>type==='bar'?d.v!==null:d.x!==null&&d.y!==null;
  function desc(data){let good=data.filter(valid);return type==='bar'?`已报合计 ${good.reduce((a,d)=>a+d.v,0)} 件（${good.length}/${data.length} 条）`:`已报 ${good.length}/${data.length} 台`}
  const mm=MembershipMotion.create({scopes,initial,duration:800,
    validate:d=>{const values=type==='bar'?[d.v]:[d.x,d.y];if(!values.every(v=>v===null||(Number.isFinite(v)&&v>=0&&v<=12)))throw new TypeError('expected null or finite in fixed scale');},
    render:f=>{
      section.querySelector('.status').textContent=f.phase==='transition'?`切换中：目标 ${f.target}；各范围显示各自真实观测，透明度不是数值。`:`${f.target} · 已稳定`;
      section.querySelector('.target').textContent=`目标 ${f.target}：${desc(scopes[f.target])}`;
      layerBox.replaceChildren();
      for(const layer of f.layers){
        const el=document.createElement('div');el.className='layer';el.dataset.scope=layer.name;el.dataset.role=layer.role;el.style.opacity=String(layer.opacity);if(layer.role!=='target')el.setAttribute('aria-hidden','true');
        const heading=document.createElement('h4');heading.textContent=`${layer.name} · ${layer.role==='target'?'目标范围':'原范围淡出'}`;el.append(heading);
        const summary=document.createElement('p');summary.className='summary';summary.textContent=desc(scopes[layer.name]);el.append(summary);
        const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 360 100');svg.setAttribute('role','img');svg.setAttribute('aria-label',type==='bar'?'数量，统一 0–12 件':'压力与温度均为 0–12 的合成坐标');
        const details=document.createElement('p');details.className='details';
        layer.marks.forEach((m,i)=>{const d=m.data;const role={retained:'保留',entered:'进入',exited:'退出'}[m.role];const missing=!valid(d);
          const text=document.createElement('span');text.dataset.id=d.id;text.dataset.role=m.role;text.textContent=`${d.id} ${role}: ${missing?'未报':type==='bar'?d.v+' 件':`(${d.x}, ${d.y})`}； `;details.append(text);
          if(missing)return;
          const mark=document.createElementNS(ns,type==='bar'?'rect':'circle');mark.dataset.id=d.id;mark.dataset.value=type==='bar'?String(d.v):`${d.x},${d.y}`;
          if(type==='bar'){mark.setAttribute('x','24');mark.setAttribute('y',String(5+i*28));mark.setAttribute('width',String(d.v/12*300));mark.setAttribute('height','16')}
          else{mark.setAttribute('cx',String(24+d.x/12*300));mark.setAttribute('cy',String(90-d.y/12*80));mark.setAttribute('r','5')}
          mark.setAttribute('fill','#187d73');svg.append(mark);
        });
        el.append(svg,details);layerBox.append(el);
      }
    }
  });
  for(const button of section.querySelectorAll('button'))button.addEventListener('click',()=>{for(const b of section.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b===button));mm.set(button.dataset.scope)});
  section.querySelector(`[data-scope="${initial}"]`).setAttribute('aria-pressed','true');return mm;
}
window.barMotion=setup('bar',barScopes,'东区','bar');window.scatterMotion=setup('scatter',scatterScopes,'早班','scatter');
</script>
```

过渡中、快速反向、初始和运行中减少动态、键盘焦点及稳定导出均须对最终页面实测。以 barMotion 或 scatterMotion 为实例，调用 `实例.withStableFrame(() => { /* 同步读取目标状态并导出 */ })`，退出时调用 `实例.destroy()`。示例本身不保证其他作品通过验证。
