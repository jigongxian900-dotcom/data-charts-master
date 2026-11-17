/* Experimental stable-ID point transition; requires ChartMotion. */
(function(root){'use strict';
function create(opts){
  if(!opts || !opts.scopes || !Object.prototype.hasOwnProperty.call(opts.scopes,opts.initial) || typeof opts.render!=='function')throw new TypeError('scopes, initial and render required');
  if(opts.duration!==undefined && (!Number.isFinite(opts.duration)||opts.duration<0))throw new RangeError('duration must be finite and nonnegative');
  const scopes=Object.create(null);
  for(const [name,records] of Object.entries(opts.scopes)){
    if(!name || !Array.isArray(records))throw new TypeError('invalid scope');const seen=new Set();
    scopes[name]=records.map(d=>{if(!d||typeof d.id!=='string'||!d.id||seen.has(d.id))throw new TypeError('stable unique ID required');seen.add(d.id);
      if(!((d.x===null&&d.y===null)||(Number.isFinite(d.x)&&Number.isFinite(d.y))))throw new TypeError('coordinates must both be finite or both missing');
      if(opts.validate)opts.validate(d,name);return Object.freeze({id:d.id,x:d.x,y:d.y});});Object.freeze(scopes[name]);
  }
  const isKnown=d=>d.x!==null&&d.y!==null;
  const observed=name=>new Set(scopes[name].filter(isKnown).map(d=>d.id));
  const sceneFor=name=>{let out=Object.create(null);for(const d of scopes[name])if(isKnown(d))out[d.id]={x:d.x,y:d.y,opacity:1};return out};
  let target=opts.initial;
  const motion=ChartMotion.create({scene:sceneFor(target),duration:opts.duration===undefined?700:opts.duration,meta:{previous:target,target},
    paint(scene,info){const m=info.meta||{previous:target,target},old=observed(m.previous),next=observed(m.target);
      const marks=Array.from(scene,([id,v])=>({id,x:v.x,y:v.y,opacity:v.opacity,role:next.has(id)?(old.has(id)?'retained':'entered'):(old.has(id)?'exited':'earlier-exit')}));
      opts.render({marks,phase:info.phase,progress:info.progress,target:m.target,previous:m.previous,targetRecords:scopes[m.target],currentValuesAreTransition:info.phase==='transition'});
    }
  });
  return {set(name){if(!Object.prototype.hasOwnProperty.call(scopes,name))throw new RangeError('unknown scope');if(name===target)return;const previous=target;target=name;
      motion.to(sceneFor(name),{meta:{previous,target},enter:(id,v)=>({x:v.x,y:v.y,opacity:0}),exit:(id,v)=>({x:v.x,y:v.y,opacity:0})});},
    isRunning:()=>motion.isRunning(),finish:()=>motion.finish(),withStableFrame:cb=>motion.withStableFrame(cb),destroy:()=>motion.destroy()};
}
root.RetainedMotion={create};
})(globalThis);
