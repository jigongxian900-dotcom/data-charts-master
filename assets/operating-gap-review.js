const slides = Array.from(document.querySelectorAll('[data-slide]'));
const materials = document.getElementById('materials');
document.querySelectorAll('a[href="#materials"]').forEach(a => a.addEventListener('click', () => { materials.open = true; }));

if (slides.length) {
  let active = 0;
  const back = document.getElementById('previous');
  const next = document.getElementById('next');
  const page = document.getElementById('page');
  const show = index => {
    active = Math.max(0, Math.min(slides.length - 1, index));
    slides.forEach((slide, i) => { slide.hidden = i !== active; });
    back.disabled = active === 0;
    next.disabled = active === slides.length - 1;
    page.value = `${active + 1} / ${slides.length}`;
  };
  back.addEventListener('click', () => show(active - 1));
  next.addEventListener('click', () => show(active + 1));
  addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.target.closest('input,textarea,select,[contenteditable]')) return;
    const targets = {ArrowLeft:active - 1,PageUp:active - 1,ArrowRight:active + 1,PageDown:active + 1,Home:0,End:slides.length - 1};
    if (!(event.key in targets)) return;
    event.preventDefault();
    show(targets[event.key]);
  });
  show(0);
}

const markets = JSON.parse(document.getElementById('market-data').textContent);
const marketButtons = Array.from(document.querySelectorAll('[data-market]'));
marketButtons.forEach(button => button.addEventListener('click', () => {
  const row = markets[button.dataset.market];
  for (const [field, value] of Object.entries(row)) {
    document.getElementById('market-'+field).textContent = field === 'attainment' ? row.attainment.toFixed(1)+'%' : value;
  }
  const track = document.getElementById('attain-track');
  track.querySelector('i').style.width = row.attainment+'%';
  track.setAttribute('aria-label', '目标达成率 '+row.attainment.toFixed(1)+'%');
  marketButtons.forEach(other => {
    other.setAttribute('aria-pressed', String(other === button));
    other.closest('tr').classList.toggle('selected', other === button);
  });
}));
document.documentElement.dataset.ready = 'true';
