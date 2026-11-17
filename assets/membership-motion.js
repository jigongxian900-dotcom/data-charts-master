/* Candidate: scoped crossfade; requires ChartMotion. No claim about data semantics. */
(function(root){'use strict';
  function create(opts){
    if(!opts || !opts.scopes || !Object.prototype.hasOwnProperty.call(opts.scopes,opts.initial) || typeof opts.render!=='function') throw new TypeError('scopes, initial and render required');
    if(opts.duration!==undefined && (!Number.isFinite(opts.duration)||opts.duration<0)) throw new RangeError('duration must be finite and nonnegative');
    const scopes=opts.scopes;
    for(const [name,scope] of Object.entries(scopes)){
      if(!name || !Array.isArray(scope) || new Set(scope.map(d=>d.id)).size!==scope.length || scope.some(d=>!d||typeof d.id!=='string'||!d.id)) throw new TypeError('each scope needs distinct stable IDs');
      if(opts.validate) scope.forEach(d=>opts.validate(d,name));
    }
    let target=opts.initial;
    const ids=name=>new Set(scopes[name].map(d=>d.id));
    const motion=ChartMotion.create({scene:{[target]:{opacity:1}},duration:opts.duration===undefined?600:opts.duration,meta:{previous:target,target},
      paint(scene,info){
        const meta=info.meta||{previous:target,target}, targetIds=ids(meta.target), previousIds=ids(meta.previous);
        const layers=Array.from(scene,([name,frame])=>({name,opacity:frame.opacity,role:name===meta.target?'target':'previous',
          marks:scopes[name].map(d=>({data:d,role:name===meta.target?(previousIds.has(d.id)?'retained':'entered'):(targetIds.has(d.id)?'retained':'exited')}))}));
        opts.render({layers,phase:info.phase,progress:info.progress,target:meta.target,previous:meta.previous});
      }
    });
    return {
      set(name){if(!Object.prototype.hasOwnProperty.call(scopes,name))throw new RangeError('unknown scope');if(name===target)return;const previous=target;target=name;
        motion.to({[name]:{opacity:1}},{meta:{previous,target},enter:()=>({opacity:0}),exit:()=>({opacity:0})});},
      finish:()=>motion.finish(),withStableFrame:fn=>motion.withStableFrame(fn),isRunning:()=>motion.isRunning(),destroy:()=>motion.destroy()
    };
  }
  root.MembershipMotion={create};
})(globalThis);
