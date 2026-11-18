const frames = Array.from(document.querySelectorAll('[data-slide]'));
const materials = document.getElementById('materials');
document.querySelectorAll('a[href="#materials"]').forEach(link => {
  link.addEventListener('click', () => { materials.open = true; });
});
if (frames.length) {
  let current = 0;
  const back = document.getElementById('back');
  const next = document.getElementById('next');
  const page = document.getElementById('page');
  function show(index) {
    current = Math.max(0, Math.min(frames.length - 1, index));
    frames.forEach((frame, i) => { frame.hidden = i !== current; });
    page.value = `${current + 1} / ${frames.length}`;
    back.disabled = current === 0;
    next.disabled = current === frames.length - 1;
  }
  back.addEventListener('click', () => show(current - 1));
  next.addEventListener('click', () => show(current + 1));
  document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.target.closest('input,textarea,select,[contenteditable]')) return;
    const indexes = {ArrowLeft:current - 1,PageUp:current - 1,ArrowRight:current + 1,PageDown:current + 1,Home:0,End:frames.length - 1};
    if (!(event.key in indexes)) return;
    event.preventDefault();
    show(indexes[event.key]);
  });
  materials.addEventListener('toggle', () => {
    if (!materials.open && location.hash === '#materials') history.replaceState(null,'',location.pathname);
  });
  show(0);
} else {
  const chapterLinks = Array.from(document.querySelectorAll('.report-rail a[href^="#chapter"]'));
  const chapters = chapterLinks.map(link => document.querySelector(link.hash));
  if (chapters.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        chapterLinks.forEach((link, i) => {
          if (chapters[i] === entry.target) link.setAttribute('aria-current','location');
          else link.removeAttribute('aria-current');
        });
      }
    },{rootMargin:'0px 0px -63% 0px'});
    chapters.forEach(chapter => observer.observe(chapter));
  }
}
document.documentElement.dataset.composeReady = 'true';
