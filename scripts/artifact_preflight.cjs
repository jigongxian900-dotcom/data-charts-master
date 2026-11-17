'use strict';
// Bounded offline artifact gate. This is not an aesthetic, data-accuracy or full a11y audit.
const fs=require('fs'), path=require('path'), {pathToFileURL}=require('url');
function loadPlaywright(){if(process.env.PLAYWRIGHT_MODULE)return require(process.env.PLAYWRIGHT_MODULE);try{return require('playwright')}catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e;return require('playwright-core');}}
const {chromium}=loadPlaywright();
async function preflight(html,options={}) {
 const contract=options.contract||{}, settle=contract.settleMs??700;
 const report={html:path.resolve(html),reducedSamples:[],checks:[],errors:[],consoleErrors:[],controls:[],motion:[],evidence:{initialReducedFrames:[],repeatedActions:[]},scope:'offline Chromium; visible buttons only; no semantic/data or aesthetics score'};
 const add=(name,status,evidence)=>report.checks.push({name,status,evidence});
 const channel=options.channel||process.env.BROWSER_CHANNEL||(process.platform==='win32'?'msedge':undefined);
 const browser=await chromium.launch({...(channel?{channel}:{}),headless:true});
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 let p; const url=pathToFileURL(path.resolve(html)).href;
 async function open(reduce='no-preference') {
  if(p)await p.close(); p=await ctx.newPage();
  p.on('pageerror',e=>report.errors.push(e.message));
  p.on('console',m=>{if(m.type()==='error')report.consoleErrors.push(m.text())});
  p.on('dialog',d=>d.dismiss());
  await p.route('**/*',r=>r.request().url()===url?r.continue():r.abort());
  await p.emulateMedia({reducedMotion:reduce});
    if(reduce==='reduce')await p.addInitScript(()=>{
   window.__artifactPreflightFrames=[];
   document.addEventListener('DOMContentLoaded',()=>{
    let n=0;function frame(){window.__artifactPreflightFrames.push({frame:n,animations:document.getAnimations().filter(a=>a.playState==='running').map(a=>({target:a.effect?.target?.tagName,id:a.effect?.target?.id,duration:a.effect?.getTiming().duration})),marks:[...document.querySelectorAll('svg path,svg rect,svg circle,[data-mark]')].slice(0,120).map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,id:e.id,d:e.getAttribute('d'),width:r.width,height:r.height,x:r.x,y:r.y,opacity:getComputedStyle(e).opacity};})});if(++n<3)requestAnimationFrame(frame);}requestAnimationFrame(frame);
   },{once:true});
  });
  await p.goto(url); await p.waitForTimeout(settle);
  if(reduce==='reduce')report.evidence.initialReducedFrames=await p.evaluate(()=>window.__artifactPreflightFrames||[]);
 }
 async function refs(phase) {
  const missing=await p.evaluate(()=>[...document.querySelectorAll('[aria-labelledby],[aria-describedby]')].flatMap(e=>['aria-labelledby','aria-describedby'].flatMap(a=>(e.getAttribute(a)||'').trim().split(/\s+/).filter(Boolean).filter(id=>!document.getElementById(id)).map(id=>({tag:e.tagName,id:e.id,attribute:a,target:id})))));
  if(missing.length)add('aria-references:'+phase,'fail',missing);
  return missing;
 }
 async function locate(c){
  const all=p.locator('button,[role="button"]');
  for(let i=0;i<await all.count();i++) {const q=all.nth(i);if(!await q.isVisible()||await q.isDisabled())continue;
   const id=await q.getAttribute('id'),text=(await q.innerText()).trim(),name=await q.getAttribute('aria-label');
   if(c.id ? id===c.id : text===c.text&&name===c.label) return q;
  }return null;
 }
  async function geometry(){return p.evaluate(()=>({marks:[...document.querySelectorAll('svg path,svg rect,svg circle,[data-mark]')].slice(0,120).map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,id:e.id,d:e.getAttribute('d'),x:r.x,y:r.y,width:r.width,height:r.height,opacity:getComputedStyle(e).opacity};}),animations:document.getAnimations().filter(a=>a.playState==='running').map(a=>({tag:a.effect?.target?.tagName,id:a.effect?.target?.id,duration:a.effect?.getTiming().duration}))}));}
 async function animations(){return p.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').map(a=>({target:a.effect?.target?.tagName,id:a.effect?.target?.id,duration:a.effect?.getTiming().duration,iterations:String(a.effect?.getTiming().iterations)})));}
 try {
  await open();const firstRefs=await refs('initial');
  const extraControls=await p.locator('select,input,textarea,a[href]').count();
  if(extraControls)add('nonbutton-controls','untested',{count:extraControls,reason:'This bounded gate does not activate selects, text inputs, links or textarea. Require a separate interaction probe.'});
  const all=p.locator('button,[role="button"]');const controls=[];
  for(let i=0;i<await all.count();i++){const q=all.nth(i);if(!await q.isVisible()||await q.isDisabled())continue;controls.push({id:await q.getAttribute('id'),text:(await q.innerText()).trim(),label:await q.getAttribute('aria-label')});}
  // Duplicate anonymous labels are ambiguous: do not pretend that all controls were tested.
  const keys=controls.map(c=>c.id?'id:'+c.id:'text:'+c.text+'|'+c.label);
  const duplicate=keys.filter((v,i)=>keys.indexOf(v)!==i);
  if(duplicate.length)add('control-identity','untested',{duplicate});
  for(const c of controls){
   await open();const q=await locate(c);if(!q){add('button:'+c.text,'untested','control cannot be located');continue;}
   await q.focus();const before=await q.evaluate(e=>document.activeElement===e);
   await q.press('Enter');await p.waitForTimeout(settle);
   const focus=await p.evaluate(()=>{const e=document.activeElement;return {tag:e?.tagName,id:e?.id,text:e&&e!==document.body?e.innerText?.trim():null,inDialog:!!e?.closest('[role="dialog"],dialog[open]')};});
   const newQ=await locate(c);const retained=newQ?await newQ.evaluate(e=>document.activeElement===e):false;
   let explicit=false;
   if(contract.focusTargets){const target=contract.focusTargets[c.id||c.text];if(target)explicit=await p.locator(target).evaluateAll(es=>es.some(e=>e===document.activeElement));}
   const ok=before&&(retained||focus.inDialog||explicit);
   report.controls.push({control:c,keyboardActivated:true,focus,ok});
   add('focus:'+ (c.id||c.text),ok?'pass':'fail',focus);
      await refs('after:'+ (c.id||c.text));
   const repeat=await locate(c);
   if(repeat){const before=await geometry();await repeat.press('Enter');const start=await geometry();await p.waitForTimeout(60);const middle=await geometry();await p.waitForTimeout(settle);const end=await geometry();report.evidence.repeatedActions.push({control:c,before,start,middle,end,note:'Second activation may be a legitimate toggle; human decides whether unchanged marks improperly replay.'});}
  }
  if(!controls.length)add('keyboard-controls',contract.requireControls?'fail':'not-applicable','No visible enabled buttons. Selects/inputs/links are not covered by this gate.');
  else add('keyboard-controls',report.controls.length===controls.length&&!duplicate.length?'pass':'untested',{tested:report.controls.length,discovered:controls.length});
  if(!firstRefs.length&&!report.checks.some(c=>c.name.startsWith('aria-references:')))add('aria-references','pass','No dangling labelledby/describedby at sampled states.');
  await open();
  const rapid=contract.rapidSelectors;
  if(Array.isArray(rapid)&&new Set(rapid).size>=2){
   for(const selector of [...rapid,...rapid.slice().reverse()]){const q=p.locator(selector);if(await q.count()!==1)throw Error('rapid selector must match one element: '+selector);await q.focus();await q.press('Enter');await p.waitForTimeout(25);}
   await p.waitForTimeout(settle);await refs('rapid');
   add('rapid-reversal','pass','Configured sequence executed; runtime/focus checked separately. Semantic final-state assertion requires contract finalText.');
   if(contract.finalText)add('rapid-final-text',(await p.locator('body').innerText()).includes(contract.finalText)?'pass':'fail',contract.finalText);
  }else add('rapid-reversal','untested','Supply at least two rapidSelectors identifying reversible controls.');
    await open('reduce');
  // Always sample the reduced page itself: zero buttons must not mean zero coverage.
  for(const frame of report.evidence.initialReducedFrames){report.reducedSamples.push({mode:'initial-reduce-frame',frame:frame.frame,active:frame.animations||[]});if(frame.animations?.length)report.motion.push({mode:'initial-reduce-frame',frame:frame.frame,active:frame.animations});}
  const initialActive=await animations();report.reducedSamples.push({mode:'initial-reduce-idle',active:initialActive});if(initialActive.length)report.motion.push({mode:'initial-reduce-idle',active:initialActive});
  for(const c of controls){const q=await locate(c);if(!q)continue;await q.press('Enter');await p.waitForTimeout(30);const active=await animations();report.reducedSamples.push({mode:'initial-reduce',control:c,active});if(active.length)report.motion.push({mode:'initial-reduce',control:c,active});await p.waitForTimeout(settle);}
    await open();
  await p.emulateMedia({reducedMotion:'reduce'});await p.waitForTimeout(50);
  const runtimeIdle=await animations();report.reducedSamples.push({mode:'runtime-reduce-idle',active:runtimeIdle});if(runtimeIdle.length)report.motion.push({mode:'runtime-reduce-idle',active:runtimeIdle});
  await p.emulateMedia({reducedMotion:'no-preference'});
  for(const c of controls){const q=await locate(c);if(!q)continue;await q.press('Enter');await p.emulateMedia({reducedMotion:'reduce'});await p.waitForTimeout(50);const active=await animations();report.reducedSamples.push({mode:'runtime-reduce',control:c,active});if(active.length)report.motion.push({mode:'runtime-reduce',control:c,active});await p.emulateMedia({reducedMotion:'no-preference'});await p.waitForTimeout(settle);}
  add('reduced-motion-css-waapi',report.motion.length?'fail':report.reducedSamples.length?'pass':'untested',report.motion.length?report.motion:'No running CSS/WAAPI animation in reduced mode at samples. Does not inspect requestAnimationFrame/canvas geometry.');
  add('motion-geometry','untested','Generic gate collected first three reduced frames and repeated-action geometry/animations, but does not infer semantic marks or replay validity. Run a chart-specific probe for motion acceptance.');
 }catch(e){add('runner','fail',String(e.stack||e));}
 finally{await browser.close();}
 add('runtime-errors',report.errors.length?'fail':'pass',[...new Set(report.errors)]);
 add('console-errors',report.consoleErrors.length?'fail':'pass',[...new Set(report.consoleErrors)]);
 const required=contract.required||['runtime-errors','console-errors','keyboard-controls','aria-references','rapid-reversal','reduced-motion-css-waapi'];
 report.required=required;
 report.blocked=report.checks.some(c=>c.status==='fail')||required.some(name=>!report.checks.some(c=>(c.name===name||c.name.startsWith(name+':'))&&['pass','not-applicable'].includes(c.status)))||report.checks.some(c=>c.status==='untested'&&required.includes(c.name));
 report.passed=!report.blocked;
 return report;
}
module.exports={preflight};
if(require.main===module){const a=process.argv.slice(2);let opts={};for(let i=0;i<a.length;i+=2)opts[a[i].replace(/^--/,'')]=a[i+1];if(!opts.html||!opts.out){console.error('node artifact_preflight.cjs --html file.html --out report.json [--contract contract.json]');process.exit(2);}preflight(opts.html,{contract:opts.contract?JSON.parse(fs.readFileSync(opts.contract,'utf8')):{}}).then(r=>{fs.writeFileSync(opts.out,JSON.stringify(r,null,2));console.log(JSON.stringify({passed:r.passed,checks:r.checks.length,errors:r.errors.length,out:opts.out}));process.exitCode=r.passed?0:1;}).catch(e=>{console.error(e);process.exitCode=2;});}
