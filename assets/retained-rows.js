/* RetainedRows candidate: DOM row-position adapter. Requires ChartMotion + RetainedMotion.
   Only filtering/reordering immutable records. Not a data-value tween or layout engine. */
(function(root){'use strict';
function create(options){
 const o=options||{}, host=o.container, doc=host&&host.ownerDocument;
 if(!host||host.nodeType!==1||host.namespaceURI!=='http://www.w3.org/1999/xhtml'||!doc||host.children.length)throw new TypeError('empty container Element required');
 if(!root.RetainedMotion||!root.ChartMotion)throw new Error('ChartMotion and RetainedMotion must be loaded first');
 if(typeof o.createRow!=='function'||!Array.isArray(o.records)||!o.scopes||typeof o.scopes!=='object')throw new TypeError('records, scopes and createRow required');
 if(!Number.isFinite(o.rowHeight)||o.rowHeight<=0||o.rowHeight>1000000)throw new RangeError('fixed rowHeight must be in (0, 1000000] CSS pixels');
 if(o.duration!==undefined&&(!Number.isFinite(o.duration)||o.duration<0))throw new RangeError('nonnegative finite duration required');
 if(o.statusElement&&(o.statusElement.nodeType!==1||o.statusElement.ownerDocument!==doc))throw new TypeError('statusElement must be an Element in this document');
 const data=new Map(), nodes=new Map(), contents=new Set(), scopes=Object.create(null);
 for(const r of o.records){if(!r||typeof r.id!=='string'||!r.id||data.has(r.id))throw new TypeError('unique nonempty record IDs required');data.set(r.id,Object.freeze({...r}));}
 for(const [name,ids] of Object.entries(o.scopes)){
  if(!name||!Array.isArray(ids))throw new TypeError('named arrays of IDs required');if(!Number.isFinite(ids.length*o.rowHeight)||ids.length*o.rowHeight>1000000)throw new RangeError('scope extent exceeds 1000000 CSS pixels');for(let i=0;i<ids.length;i++)if(!(i in ids))throw new TypeError('sparse scope arrays are not supported');const seen=new Set();
  scopes[name]=ids.map((id,i)=>{if(typeof id!=='string'||!data.has(id)||seen.has(id))throw new TypeError('scope IDs must be unique known records');seen.add(id);return {id,x:0,y:i*o.rowHeight};});
 }
 if(!Object.prototype.hasOwnProperty.call(scopes,o.initial))throw new RangeError('unknown initial scope');
 if(o.fallbackFocus&&(typeof o.fallbackFocus.focus!=='function'||o.fallbackFocus.ownerDocument!==doc))throw new TypeError('fallbackFocus must be a focusable element in this document');
 // Build once. Filtering never calls createRow or changes any inner chart's geometry.
 for(const [id,r] of data){
  const content=o.createRow(r);
  if(!content||content.nodeType!==1||content.ownerDocument!==doc||content.isConnected||contents.has(content))throw new TypeError('createRow must return a distinct detached Element');contents.add(content);
  const row=doc.createElement('div');row.className='retained-row';row.dataset.rowId=id;row.setAttribute('role','listitem');
  Object.assign(row.style,{position:'absolute',left:'0',right:'0',top:'0',height:o.rowHeight+'px',boxSizing:'border-box',opacity:'0',transform:'translateY(0px)',transition:'none',animation:'none'});
  row.append(content);nodes.set(id,row);
 }
 const original={style:host.getAttribute('style'),role:host.getAttribute('role'),tabindex:host.getAttribute('tabindex'),'data-retained-scope':host.getAttribute('data-retained-scope'),'data-retained-phase':host.getAttribute('data-retained-phase')};
 host.style.position='relative';host.setAttribute('role','list');if(!host.hasAttribute('tabindex'))host.setAttribute('tabindex','-1');
 let target=o.initial,destroyed=false,motion;
 function focusFallback(){const f=o.fallbackFocus&&o.fallbackFocus.isConnected?o.fallbackFocus:host;f.focus({preventScroll:true});if(doc.activeElement!==f&&!f.contains(doc.activeElement))host.focus({preventScroll:true});}
 function arrange(name){
  const ids=scopes[name].map(r=>r.id), keep=new Set(ids), focused=doc.activeElement;
  const exitingFocus=[...nodes].some(([id,n])=>!keep.has(id)&&n.contains(focused));
  if(exitingFocus)focusFallback();
  // Reuse exact nodes. DOM order follows final reading order; restore retained descendant focus after moves.
  for(const id of ids)host.append(nodes.get(id));
  if(!exitingFocus&&focused&&focused!==doc.body&&focused.isConnected&&host.contains(focused))focused.focus({preventScroll:true});
  for(const [id,node] of nodes){const present=keep.has(id);node.inert=!present;node.setAttribute('aria-hidden',String(!present));if(present){node.setAttribute('aria-posinset',String(ids.indexOf(id)+1));node.setAttribute('aria-setsize',String(ids.length));}}
 }
 arrange(target);
 motion=root.RetainedMotion.create({scopes,initial:target,duration:o.duration===undefined?420:o.duration,render(frame){
  const keep=new Set(), targetIds=new Set(scopes[target].map(r=>r.id));let extent=scopes[target].length*o.rowHeight;
  for(const mark of frame.marks){
   const node=nodes.get(mark.id);keep.add(mark.id);if(node.parentNode!==host)host.append(node);
   node.style.transform='translateY('+mark.y+'px)';node.style.opacity=String(mark.opacity);node.dataset.membership=mark.role;
   node.inert=!targetIds.has(mark.id);node.setAttribute('aria-hidden',String(!targetIds.has(mark.id)));
   extent=Math.max(extent,mark.y+o.rowHeight);
  }
  for(const [id,node] of nodes)if(node.parentNode===host&&!keep.has(id)){if(node.contains(doc.activeElement))focusFallback();node.remove();}
  host.style.height=(frame.phase==='transition'?extent:scopes[target].length*o.rowHeight)+'px';
  host.dataset.retainedScope=target;host.dataset.retainedPhase=frame.phase;
  if(o.statusElement)o.statusElement.textContent=frame.phase==='transition'?'范围切换中：只改变行位置与成员可见性，数值保持不变。':'范围：'+target+'；'+scopes[target].length+'项，数值保持不变。';
 }});
 function alive(){if(destroyed)throw new Error('RetainedRows has been destroyed');}
 return {set(name){alive();if(!Object.prototype.hasOwnProperty.call(scopes,name))throw new RangeError('unknown scope');if(name===target)return false;target=name;arrange(name);motion.set(name);return true;},
  finish(){alive();return motion.finish();},withStableFrame(fn){alive();return motion.withStableFrame(fn);},isRunning(){return !destroyed&&motion.isRunning();},
  getNode(id){return nodes.get(id)||null;},
  destroy(){if(destroyed)return;motion.destroy();destroyed=true;if(host.contains(doc.activeElement))focusFallback();for(const n of nodes.values())n.remove();for(const [key,value] of Object.entries(original)){if(value===null)host.removeAttribute(key);else host.setAttribute(key,value);}}
 };
}
root.RetainedRows={create};
})(globalThis);
