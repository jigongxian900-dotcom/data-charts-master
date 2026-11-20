(() => {
  'use strict';
  const $ = (s, el=document) => el.querySelector(s);
  const $$ = (s, el=document) => [...el.querySelectorAll(s)];
  const scenes = $$('.stage .scene');
  const stage = $('.stage');
  const dock = $('.dockbar');
  const nav = $('.peek');
  const gallery = $('#overview');
  const sources = $('#sources');
  const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
  const variants = JSON.parse($('#variants')?.textContent ?? '{}');
  let current = -1;
  let dockTimer;
  let playTimer;
  let playing = false;
  let gesture;

  function fit() {
    const scale = Math.min(window.innerWidth/1600, window.innerHeight/900);
    document.documentElement.style.setProperty('--scale', scale);
    if(gallery.open) sizeThumbnails();
  }

  function playMotion(scene) {
    scene.classList.remove('moving');
    if (motionPreference.matches || scene.dataset.motion === 'idle') return;
    void scene.offsetWidth;
    scene.classList.add('moving');
  }

  function schedule() {
    clearTimeout(playTimer);
    if (!playing) return;
    playTimer = setTimeout(() => {
      if (current === scenes.length-1) {
        auto(false);
      } else {
        show(current+1);
      }
    }, scenes[current].dataset.motion === 'idle' ? 7600 : 9400);
  }

  function auto(run) {
    playing = run;
    $('#auto').textContent = playing ? '停连播' : '连播';
    $('#auto').setAttribute('aria-pressed', String(playing));
    if (playing) schedule();
    else clearTimeout(playTimer);
  }

  function show(index) {
    if (!Number.isFinite(index)) return;
    const i = Math.max(0,Math.min(scenes.length-1,Math.trunc(index)));
    if (i === current) return;
    const old = scenes[current];
    if (old) {
      if (old.contains(document.activeElement)) stage.focus({preventScroll:true});
      old.hidden = true;
      old.classList.remove('moving');
    } else {
      scenes.forEach((scene,j)=>{scene.hidden = j!==i;});
    }
    current = i;
    const scene = scenes[i];
    scene.hidden = false;
    syncSurround(scene);
    $('#count').textContent = String(i+1).padStart(2,'0')+' / '+scenes.length;
    $('#announcement').textContent = `第 ${i+1} 页，${scene.dataset.label}`;
    $('#prev').disabled = i===0;
    $('#next').disabled = i===scenes.length-1;
    history.replaceState(null,'','#'+(i+1));
    playMotion(scene);
    schedule();
  }

  function syncSurround(scene) {
    const canvas = stage.closest('.viewport');
    if (canvas) canvas.style.setProperty('--stage-surround', getComputedStyle(scene).backgroundColor);
  }

  function copyThumb(scene) {
    const clone=scene.cloneNode(true);
    clone.hidden=false;
    clone.classList.remove('moving');
    clone.inert=true;
    $$('button,a',clone).forEach(el=>{
      const inert=document.createElement('span');
      inert.className=el.className;
      inert.append(...el.childNodes);
      el.replaceWith(inert);
    });
    $$('[id]',clone).forEach(el=>el.removeAttribute('id'));
    const wrapper=document.createElement('span');
    wrapper.className='thumb-frame';
    wrapper.setAttribute('aria-hidden','true');
    wrapper.append(clone);
    return wrapper;
  }

  function sizeThumbnails() {
    $$('.thumb-frame',gallery).forEach(el=>el.style.setProperty('--thumb-scale',el.clientWidth/1600));
  }

  function openGallery() {
    if(gallery.open){gallery.close();return;}
    closePlayback();
    const list = $('.gallery',gallery);
    list.replaceChildren();
    scenes.forEach((scene, index) => {
      const button=document.createElement('button');
      button.type='button';
      button.setAttribute('aria-current',String(index===current));
      button.setAttribute('aria-label',`第 ${index+1} 页 ${scene.dataset.label}`);
      button.append(copyThumb(scene));
      const number=document.createElement('b');
      number.textContent=String(index+1).padStart(2,'0');
      button.append(number,scene.dataset.label);
      button.addEventListener('click',()=>{gallery.close();show(index);stage.focus({preventScroll:true})});
      list.append(button);
    });
    gallery.showModal();
    sizeThumbnails();
    $('[aria-current="true"]',gallery)?.focus({preventScroll:true});
  }

  function closePlayback() {
    auto(false);
  }

  function setVariant(button) {
    const [name, value] = button.dataset.variant.split(':');
    if (button.getAttribute('aria-pressed') === 'true') return;
    const config = variants[name]?.[value];
    if (!config) return;
    closePlayback();
    const scene = scenes[current];
    scene.classList.remove('moving');
    scene.dataset.state=value;
    $$('.chooser button',scene).forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    for (const [selector,text] of Object.entries(config.text ?? {})) {
      const node = $(selector,scene);
      if (node) node.textContent=text;
    }
    for (const [selector,markup] of Object.entries(config.html ?? {})) {
      const node = $(selector,scene);
      if (node) node.innerHTML=markup;
    }
    syncSurround(scene);
    if (config.replay) playMotion(scene);
  }

  async function fullScreen() {
    try{
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    }catch{
      $('#announcement').textContent = '当前窗口未启用全屏。';
      wakeDock();
    }
  }

  function wakeDock() {
    dock.classList.add('shown');
    nav.classList.add('revealed');
    clearTimeout(dockTimer);
    dockTimer=setTimeout(()=>{dock.classList.remove('shown');nav.classList.remove('revealed')},2500);
  }

  document.addEventListener('click',event=>{
    const button=event.target.closest('button');
    if(!button) return;
    if(button.hasAttribute('data-go')){closePlayback();show(Number(button.dataset.go));return;}
    if(button.hasAttribute('data-variant')){setVariant(button);return;}
    const action=button.dataset.action;
    if(action==='prev'||action==='next'){closePlayback();show(current+(action==='next'?1:-1));}
    if(action==='replay'){closePlayback();playMotion(scenes[current]);}
    if(action==='overview')openGallery();
    if(action==='sources'&&sources){closePlayback();sources.showModal();}
    if(action==='auto')auto(!playing);
    if(action==='full')fullScreen();
  });

  window.addEventListener('keydown',event=>{
    if (gallery.open||sources?.open||event.altKey||event.ctrlKey||event.metaKey) return;
    const key=event.key.toLowerCase();
    if (key==='o'||key==='c'){event.preventDefault();openGallery();}
    else if (key==='r'){closePlayback();playMotion(scenes[current]);}
    else if (key==='f'){fullScreen();}
    else if (key==='p'){auto(!playing);wakeDock();}
    else if (key==='?'||key==='escape'){wakeDock();}
    else if (['arrowright','arrowleft','pagedown','pageup','home','end',' '].includes(key)) {
      if (event.target.closest('input,select,textarea,button,a') && key===' ') return;
      event.preventDefault();
      closePlayback();
      show(key==='home'?0:key==='end'?scenes.length-1:current+(['arrowright','pagedown',' '].includes(key)?1:-1));
    }
  });

  window.addEventListener('pointermove',event=>{if(event.clientY>window.innerHeight-55||event.clientY<48&&event.clientX>window.innerWidth-100)wakeDock()});
  stage.addEventListener('pointerdown',event=>{
    if(event.pointerType==='touch'&&!event.target.closest('button,a'))gesture={x:event.clientX,y:event.clientY,id:event.pointerId};
  });
  stage.addEventListener('pointerup',event=>{
    if(gesture?.id!==event.pointerId)return;
    const dx=event.clientX-gesture.x,dy=event.clientY-gesture.y;gesture=null;
    if(Math.abs(dx)>44&&Math.abs(dx)>Math.abs(dy)*1.2){closePlayback();show(current+(dx<0?1:-1))}
    else wakeDock();
  });
  stage.addEventListener('pointercancel',()=>{gesture=null});
  window.addEventListener('resize',fit);
  function openFromAddress(){
    show(Math.min(scenes.length,Math.max(1,Number.parseInt(location.hash.slice(1),10)||1))-1);
  }
  window.addEventListener('hashchange',()=>{closePlayback();openFromAddress()});
  motionPreference.addEventListener('change',()=>{if(motionPreference.matches)scenes[current].classList.remove('moving')});
  window.addEventListener('beforeprint',closePlayback);
  fit();
  openFromAddress();
})();
