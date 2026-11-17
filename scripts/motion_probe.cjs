#!/usr/bin/env node
'use strict';
// Local evidence collector; the optional gate checks only explicitly declared linear mappings.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

function checkMapping(item, m) {
  const review = reason => ({ status:'review-required', reason });
  if (!m || typeof m !== 'object' || !['svg-width-attribute','box-width-px'].includes(m.geometry) ||
      typeof m.mark !== 'string' || typeof m.value !== 'string' || typeof m.unit !== 'string' || !m.unit.trim() ||
      typeof m.suffix !== 'string' || !Number.isFinite(m.unitsPerValue) || m.unitsPerValue <= 0 ||
      !Number.isFinite(m.from) || !Number.isFinite(m.to) || m.from < 0 || m.to < 0 || m.from === m.to ||
      !Number.isFinite(m.tolerance) || m.tolerance <= 0 || m.tolerance >= Math.abs(m.to-m.from)*0.1)
    return review('Invalid or unsupported declaration: require a nonnegative linear zero-baseline width, unit, suffix, distinct endpoints and bounded value tolerance.');
  const frames=['before','start','middle','end','reducedAfter','reducedEnd','reducedRuntimeShort','reducedRuntimeEnd'];
  const samples={};
  for (const name of frames) {
    const f=item.frames[name], marks=f?.selectors[m.mark], values=f?.selectors[m.value];
    if (!marks || !values || marks.length !== 1 || values.length !== 1 || !marks[0].visible || !values[0].visible)
      return review(`${name}: expected exactly one visible mark and value for declared selector names.`);
    const text=values[0].text;
    if (m.suffix && !text.endsWith(m.suffix)) return review(`${name}: value suffix does not match declared unit format.`);
    const raw=m.suffix ? text.slice(0,-m.suffix.length).trim() : text.trim();
    if (!/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(raw)) return review(`${name}: unsupported or negative numeric label.`);
    const value=Number(raw), rawWidth=m.geometry === 'svg-width-attribute' ? marks[0].attributes.width : marks[0].box.width;
    if (rawWidth === undefined || rawWidth === null || !/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(String(rawWidth))) return review(`${name}: width is missing or unsupported.`);
    const width=Number(rawWidth), represented=width/m.unitsPerValue;
    if (!Number.isFinite(value) || !Number.isFinite(represented)) return review(`${name}: non-finite value or width.`);
    samples[name]={value,width,represented,difference:value-represented,timestamp:f.timestamp};
  }
  const failures=[];
  for (const [name,s] of Object.entries(samples)) {
    if (Math.abs(s.difference)>m.tolerance) failures.push(`${name}: label and width differ beyond tolerance`);
    if (s.value < Math.min(m.from,m.to)-m.tolerance || s.value > Math.max(m.from,m.to)+m.tolerance) failures.push(`${name}: value outside declared endpoint range`);
  }
  for (const [name,target] of Object.entries({before:m.from,end:m.to,reducedAfter:m.to,reducedEnd:m.to,reducedRuntimeShort:m.to,reducedRuntimeEnd:m.to}))
    if (Math.abs(samples[name].value-target)>m.tolerance || Math.abs(samples[name].represented-target)>m.tolerance) failures.push(`${name}: not at declared target ${target}`);
  if (failures.length) return {status:'fail',failures,samples};
  const isIntermediate = s => Math.abs(s.value-m.from)>m.tolerance && Math.abs(s.value-m.to)>m.tolerance;
  if (!isIntermediate(samples.start) && !isIntermediate(samples.middle)) return {status:'review-required',reason:'No measurable intermediate frame; a static or missed transition cannot pass.',samples};
  return {status:'pass',scope:'Declared single linear zero-baseline width mapping only; manual review remains required.',samples};
}

async function main() {
  const [configPath, outArg] = process.argv.slice(2);
  if (!configPath || !outArg) throw Error('Usage: node motion_probe.cjs <config.json> <output-directory>');
  let chromium;
  try { ({ chromium } = require('playwright')); }
  catch { throw Error('Playwright unavailable. Use existing local Playwright installation, or record the same states manually; see autonomous-quality-loop.md.'); }
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  if (!config.file || !Array.isArray(config.actions) || !config.actions.length || !config.selectors || !Object.keys(config.selectors).length) throw Error('Require file, nonempty actions, and named selectors.');
  const target = path.resolve(path.dirname(path.resolve(configPath)), config.file);
  const out = path.resolve(outArg); fs.mkdirSync(out, { recursive: true });
  const executablePath = config.browserExecutable || (process.platform === 'win32' && [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
  ].find(p => fs.existsSync(p)));
  let browser;
  try { browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) }); }
  catch (e) { throw Error(`Cannot start a local browser: ${e.message}\nSet browserExecutable in config, or use the documented manual recording alternative.`); }
  const report = { file: target, time: new Date().toISOString(), limitations: ['No automatic business or scale inference; optional consistency checks cover only the declared single linear width mapping, not the whole chart.', 'Screenshots follow measurements; capture overhead and browser scheduling affect frame timing.', 'Selectors cover DOM/SVG only; canvas needs author-provided visible state or manual inspection.'], actions: [] };
  try {
    const context = await browser.newContext({ viewport: config.viewport || { width: 1200, height: 800 } });
    // Never transmit page data by default. Local files remain available to the page.
    await context.route('**/*', route => {
      const url = route.request().url();
      if (url.startsWith('file:') || url.startsWith('data:') || url.startsWith('blob:')) return route.continue();
      return route.abort();
    });
    const page = await context.newPage();
    const errors = []; page.on('pageerror', e => errors.push(String(e)));
    async function open(reduced = false) {
      await page.emulateMedia({ reducedMotion: reduced ? 'reduce' : 'no-preference' });
      await page.goto(pathToFileURL(target).href, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
    }
    async function record(name) {
      const data = await page.evaluate(selectors => {
        const visible = e => { const r=e.getBoundingClientRect(), s=getComputedStyle(e); return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) > 0; };
        const round = n => Math.round(n * 100) / 100;
        const found = {};
        for (const [name, selector] of Object.entries(selectors)) found[name] = [...document.querySelectorAll(selector)].map(e => {
          const r=e.getBoundingClientRect(), attrs={};
          for(const key of ['id','data-id','data-mark','aria-pressed','aria-selected','aria-valuenow','width','height','x','y','cx','cy','r','d','transform']) if(e.hasAttribute(key)) attrs[key]=e.getAttribute(key);
          return { visible:visible(e), text:(e.innerText ?? e.textContent ?? '').trim().slice(0,1000), box:{x:round(r.x),y:round(r.y),width:round(r.width),height:round(r.height)}, attributes:attrs };
        });
        const active=document.activeElement;
        return { timestamp:performance.now(), focus:active ? {tag:active.tagName,id:active.id,text:(active.innerText || '').trim().slice(0,100),ariaPressed:active.getAttribute('aria-pressed')} : null, selectors:found };
      }, config.selectors);
      await page.screenshot({ path:path.join(out, `${name}.png`) });
      data.screenshot = `${name}.png`; return data;
    }
    for (let i=0; i<config.actions.length; i++) {
      const a=config.actions[i], ms=a.durationMs ?? 700, midpoint=a.midpointMs ?? Math.round(ms/2), prefix=String(i+1).padStart(2,'0');
      if (!a.trigger || !a.reverse || midpoint <= 0 || midpoint >= ms) throw Error(`Action ${i+1}: require trigger, reverse and 0 < midpointMs < durationMs`);
      const item={ name:a.name || prefix, declared:a, frames:{} }; report.actions.push(item);
      await open(); item.frames.before=await record(`${prefix}-before`);
      await page.locator(a.trigger).first().click();
      // Record the first reachable post-action state as well as the old state.
      // Screenshot time is charged against the requested sampling interval.
      const startedAt=await page.evaluate(() => performance.now());
      item.frames.start=await record(`${prefix}-start`);
      let elapsed=(await page.evaluate(() => performance.now()))-startedAt;
      await page.waitForTimeout(Math.max(0,midpoint-elapsed)); item.frames.middle=await record(`${prefix}-middle`);
      elapsed=(await page.evaluate(() => performance.now()))-startedAt;
      await page.waitForTimeout(Math.max(0,ms-elapsed)+100); item.frames.end=await record(`${prefix}-end`);
      await open(); await page.locator(a.trigger).first().click(); await page.waitForTimeout(midpoint);
      item.frames.interruptBefore=await record(`${prefix}-interrupt-before`);
      await page.locator(a.reverse).first().click(); item.frames.interruptAfter=await record(`${prefix}-interrupt-after`);
      await page.waitForTimeout(ms+100); item.frames.interruptEnd=await record(`${prefix}-interrupt-end`);
      await open(true); item.frames.reducedBefore=await record(`${prefix}-reduced-before`);
      await page.locator(a.trigger).first().click(); item.frames.reducedAfter=await record(`${prefix}-reduced-after`);
      await page.waitForTimeout(ms+100); item.frames.reducedEnd=await record(`${prefix}-reduced-end`);
      await open(); await page.locator(a.trigger).first().click(); await page.waitForTimeout(midpoint);
      await page.emulateMedia({ reducedMotion:'reduce' }); item.frames.reducedRuntime=await record(`${prefix}-reduced-runtime`);
      await page.waitForTimeout(100); item.frames.reducedRuntimeShort=await record(`${prefix}-reduced-runtime-short`);
      await page.waitForTimeout(ms+100); item.frames.reducedRuntimeEnd=await record(`${prefix}-reduced-runtime-end`);
      item.semanticGate = a.semanticMapping === undefined ? { status:'not-checked', reason:'No explicit mapping declared.' } : checkMapping(item, a.semanticMapping);
    }
    report.pageErrors=errors;
    report.missingSelectors = report.actions.flatMap(a => Object.entries(a.frames).flatMap(([frame, data]) => Object.entries(data.selectors).filter(([, matches]) => !matches.length).map(([selector]) => ({ action:a.name, frame, selector }))));
    if (errors.length) for (const a of report.actions) if (a.semanticGate.status === 'pass') a.semanticGate = { ...a.semanticGate, status:'review-required', reason:'Page errors occurred during capture.' };
    await context.close();
  } finally { await browser.close(); fs.writeFileSync(path.join(out,'evidence.json'),JSON.stringify(report,null,2)); }
  console.log(`Evidence saved: ${path.join(out,'evidence.json')} (${report.actions.length} action(s); ${report.pageErrors?.length ?? 0} page errors; ${report.missingSelectors?.length ?? 0} missing selector instances). Review required.`);
}
main().catch(e => { console.error(e.stack || e); process.exitCode=1; });
