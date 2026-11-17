'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const Motion = require('../assets/chart-motion.js');

function harness(options = {}) {
  let time = 0, serial = 0;
  const queued = new Map(), cancelled = new Map(), listeners = new Map(), mediaListeners = new Set();
  const media = { matches: !!options.reduced,
    addEventListener(type, fn) { mediaListeners.add(fn); },
    removeEventListener(type, fn) { mediaListeners.delete(fn); } };
  const eventTarget = { addEventListener(type, fn) { listeners.set(type, fn); }, removeEventListener(type, fn) { if (listeners.get(type) === fn) listeners.delete(type); } };
  const paints = [], settled = [];
  const controller = Motion.create({ scene: options.scene || { alpha: { x: 0 } }, duration: 100,
    ...options,
    paint(value, info) { paints.push({ value, info }); options.paint?.(value, info); },
    onSettled(value, info) { settled.push({ value, info }); options.onSettled?.(value, info); },
    environment: { now: () => time, requestFrame(fn) { queued.set(++serial, fn); return serial; },
      cancelFrame(id) { if (queued.has(id)) cancelled.set(id, queued.get(id)); queued.delete(id); }, mediaQuery: media, eventTarget } });
  return { controller, paints, settled, queued, cancelled, listeners, mediaListeners,
    step(ms) { time += ms; const callbacks = [...queued.values()]; queued.clear(); callbacks.forEach(fn => fn()); },
    reduce(value) { media.matches = value; [...mediaListeners].forEach(fn => fn({ matches: value })); },
    event(type) { listeners.get(type)?.(); }, visible(id = 'alpha') { return paints.at(-1).value.get(id); } };
}
test('paints a real middle frame and a final frame', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }); h.step(25);
  assert.equal(h.visible().x, 25); assert.equal(h.controller.snapshot().get('alpha').x, 25);
  h.step(75); assert.equal(h.visible().x, 100); assert.equal(h.settled.length, 1); assert.equal(h.queued.size, 0);
});
test('stable ID correspondence survives target reordering', () => {
  const h = harness({ scene: new Map([['a', { x: 10 }], ['b', { x: 100 }]]) });
  h.controller.to(new Map([['b', { x: 200 }], ['a', { x: 30 }]])); h.step(50);
  assert.equal(h.visible('a').x, 20); assert.equal(h.visible('b').x, 150);
});
test('rapid reversal starts exactly at the visible frame', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }); h.step(40);
  h.controller.to({ alpha: { x: 0 } }); assert.equal(h.visible().x, 40);
  h.step(50); assert.equal(h.visible().x, 20); h.step(50); assert.equal(h.visible().x, 0);
});
test('generation rejects callbacks even when RAF cancellation loses a race', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } });
  h.controller.to({ alpha: { x: 60 } }); const before = h.paints.length;
  [...h.cancelled.values()].forEach(fn => fn()); assert.equal(h.paints.length, before);
  h.step(50); assert.equal(h.visible().x, 30);
});
test('paint reentry preserves its replacement transition and one frame loop', () => {
  let h, switched = false;
  h = harness({ paint(value, info) {
    if (info.reason === 'frame' && !switched) { switched = true; h.controller.to({ alpha: { x: 0 } }); }
  } });
  h.controller.to({ alpha: { x: 100 } }); h.step(40); assert.equal(h.visible().x, 40);
  assert.equal(h.queued.size, 1); h.step(50); assert.equal(h.visible().x, 20); h.step(50); assert.equal(h.settled.length, 1);
});
test('onStart reentry supersedes outer request without painting it', () => {
  let h, switched = false;
  h = harness({ onStart() { if (!switched) { switched = true; h.controller.to({ alpha: { x: 30 } }); } } });
  h.controller.to({ alpha: { x: 100 } }); h.step(100);
  assert.equal(h.visible().x, 30); assert.equal(h.settled.length, 1);
});
test('onSettled reentry survives finishing outer transition', () => {
  let h, switched = false;
  h = harness({ onSettled() { if (!switched) { switched = true; h.controller.to({ alpha: { x: 80 } }); } } });
  h.controller.to({ alpha: { x: 40 } }); h.step(100); assert.equal(h.controller.isRunning(), true);
  h.step(50); assert.equal(h.visible().x, 60); h.step(50); assert.equal(h.visible().x, 80);
});
test('cancel freezes the visible frame; finish synchronously paints the target', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }); h.step(35); h.controller.cancel();
  h.step(100); assert.equal(h.visible().x, 35); assert.equal(h.controller.target().get('alpha').x, 100);
  h.controller.to({ alpha: { x: 80 } }); const result = h.controller.finish();
  assert.equal(result.get('alpha').x, 80); assert.equal(h.visible().x, 80); assert.equal(h.controller.isRunning(), false);
});
test('stable export includes reentrant settled changes without an active animation', () => {
  let h, changed = false;
  h = harness({ onSettled() { if (!changed) { changed = true; h.controller.to({ alpha: { x: 75 } }); } } });
  h.controller.to({ alpha: { x: 100 } }); h.step(20);
  const output = h.controller.withStableFrame(value => ({ x: value.get('alpha').x, visible: h.visible().x, running: h.controller.isRunning() }));
  assert.deepEqual(output, { x: 75, visible: 75, running: false });
});
test('initial and runtime reduced motion settle immediately; disabling permits animation', () => {
  const h = harness({ reduced: true }); h.controller.to({ alpha: { x: 50 } }); assert.equal(h.visible().x, 50); assert.equal(h.queued.size, 0);
  h.reduce(false); h.controller.to({ alpha: { x: 100 } }); h.step(20); assert.equal(h.visible().x, 60);
  h.reduce(true); assert.equal(h.visible().x, 100); assert.equal(h.queued.size, 0);
  assert.equal(h.settled.at(-1).info.reason, 'reduced-motion');
});
test('beforeprint paints the stable target and afterprint preserves it', () => {
  const h = harness(); h.controller.to({ alpha: { x: 120 } }, { meta: { view: 'filtered' } }); h.step(15);
  h.event('beforeprint'); assert.equal(h.visible().x, 120); h.event('afterprint'); assert.equal(h.visible().x, 120);
  assert.equal(h.paints.at(-1).info.meta.view, 'filtered'); assert.equal(h.controller.isRunning(), false);
});
test('destroy removes listeners, cancels callbacks and refuses new transitions', () => {
  const h = harness(); h.controller.to({ alpha: { x: 20 } }); const before = h.paints.length; h.controller.destroy();
  assert.equal(h.listeners.size, 0); assert.equal(h.mediaListeners.size, 0); assert.equal(h.queued.size, 0);
  [...h.cancelled.values()].forEach(fn => fn()); h.reduce(true); assert.equal(h.paints.length, before);
  assert.throws(() => h.controller.to({}), /destroyed/); h.controller.destroy();
});
test('enter and exit hooks animate IDs explicitly and remove exiting ID only on settle', () => {
  const h = harness({ scene: { old: { x: 60 } }, enter: (id, to) => ({ x: 0 }), exit: (id, from) => ({ x: 0 }) });
  h.controller.to({ added: { x: 80 } }); h.step(50);
  assert.equal(h.visible('old').x, 30); assert.equal(h.visible('added').x, 40);
  h.step(50); assert.equal(h.visible('old'), undefined); assert.equal(h.visible('added').x, 80);
});
test('default membership switches immediately; empty scene is valid', () => {
  const h = harness(); h.controller.to({ new: { x: 10 } });
  assert.equal(h.visible('alpha'), undefined); assert.equal(h.visible('new').x, 10);
  h.controller.finish(); h.controller.to({}); assert.equal(h.paints.at(-1).value.size, 0); h.controller.finish();
  assert.equal(h.controller.snapshot().size, 0);
});
test('no-op and zero duration settle without scheduling frames', () => {
  const h = harness(); h.controller.to({ alpha: { x: 0 } }); assert.equal(h.queued.size, 0);
  h.controller.to({ alpha: { x: 80 } }, { duration: 0 }); assert.equal(h.visible().x, 80); assert.equal(h.queued.size, 0);
});
test('invalid requests leave the currently running transition intact', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }); h.step(20);
  for (const value of [NaN, Infinity, -Infinity]) assert.throws(() => h.controller.to({ alpha: { x: value } }), /finite/);
  for (const duration of [NaN, Infinity, -1]) assert.throws(() => h.controller.to({ alpha: { x: 2 } }, { duration }), /duration/);
  assert.throws(() => h.controller.to(new Map([[1, { x: 3 }]])), /IDs/);
  assert.equal(h.visible().x, 20); h.step(30); assert.equal(h.visible().x, 50);
});
test('nested numeric interpolation tolerates reordered keys without losing static fields', () => {
  const h = harness({ scene: { alpha: { kind: 'bar', p: [0, { a: 10, b: 20 }] } } });
  h.controller.to({ alpha: { p: [20, { b: 40, a: 30 }], kind: 'bar' } }); h.step(50);
  assert.equal(h.visible().p[0], 10); assert.equal(h.visible().p[1].a, 20); assert.equal(h.visible().p[1].b, 30);
});
test('incompatible path, array, string and object shapes require an explicit author adapter', () => {
  const h = harness({ scene: { alpha: { d: 'M0 0L1 1' } } });
  assert.throws(() => h.controller.to({ alpha: { d: 'M0 0C1 1 2 2 3 3' } }), /SVG path/);
  assert.throws(() => h.controller.to({ alpha: { d: [0, 1] } }), /incompatible/);
  assert.throws(() => h.controller.to({ alpha: { other: 1 } }), /incompatible/);
  h.controller.to({ alpha: { d: 'M2 2' } }, { interpolate: (a, b, t) => t < 0.5 ? a : b });
  h.step(50); assert.equal(h.visible().d, 'M2 2');
});
test('bad custom frames fail without storing nonfinite geometry or keeping a loop alive', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }, { interpolate: () => ({ x: NaN }) });
  assert.throws(() => h.step(50), /finite/); assert.equal(h.visible().x, 0); assert.equal(h.controller.isRunning(), false); assert.equal(h.queued.size, 0);
});
test('snapshot, target, paint and interpolation arguments do not expose mutable internal scenes', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } });
  h.controller.snapshot().get('alpha').x = 600; h.controller.target().clear(); h.paints.at(-1).value.get('alpha').x = 700;
  h.step(50); assert.equal(h.visible().x, 50); assert.equal(h.controller.target().get('alpha').x, 100);
});
test('large opposite finite endpoints produce a finite midpoint', () => {
  const h = harness({ scene: { alpha: { x: -1e308 } } }); h.controller.to({ alpha: { x: 1e308 } }); h.step(50); assert.equal(h.visible().x, 0);
});
test('throwing start callbacks do not leave an unfinishable active job', () => {
  const h = harness({ onStart() { throw new Error('author error'); } });
  assert.throws(() => h.controller.to({ alpha: { x: 50 } }), /author error/);
  assert.equal(h.controller.isRunning(), false); assert.equal(h.queued.size, 0); assert.equal(h.controller.target().get('alpha').x, 50);
  h.controller.finish(); assert.equal(h.visible().x, 50);
});
test('bad ease does not create a runaway loop', () => {
  const h = harness(); h.controller.to({ alpha: { x: 40 } }, { ease: () => Infinity });
  assert.throws(() => h.step(50), /ease/); assert.equal(h.controller.isRunning(), false); assert.equal(h.visible().x, 0);
});
test('static SVG path may accompany numeric transforms without parsing path numbers', () => {
  const h = harness({ scene: { alpha: { d: 'M0 0L10 10Z', x: 0 } } });
  h.controller.to({ alpha: { d: 'M0 0L10 10Z', x: 50 } }); h.step(50);
  assert.equal(h.visible().d, 'M0 0L10 10Z'); assert.equal(h.visible().x, 25);
});
test('custom interpolator reentry cannot overwrite its replacement frame', () => {
  const h = harness(); let once = false;
  h.controller.to({ alpha: { x: 100 } }, { interpolate(a, b, t) {
    if (!once) { once = true; h.controller.to({ alpha: { x: 60 } }); }
    return { x: 999 };
  } });
  h.step(50); assert.equal(h.visible().x, 0); assert.equal(h.queued.size, 1);
  h.step(50); assert.equal(h.visible().x, 30);
});
test('ease reentry can cancel without later writing a stale frame', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }, { ease(t) { h.controller.cancel(); return t; } });
  h.step(50); assert.equal(h.visible().x, 0); assert.equal(h.controller.isRunning(), false);
});
test('sparse arrays are rejected rather than silently changing shape', () => {
  assert.throws(() => harness({ scene: { a: Array(2) } }), /sparse/);
});
test('cancel notifies paint of the frozen state and does not claim settled target values', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }); h.step(50); h.controller.cancel();
  assert.equal(h.paints.at(-1).info.phase, 'cancelled'); assert.equal(h.paints.at(-1).info.reason, 'cancel');
  assert.equal(h.paints.at(-1).info.progress, 0.5); assert.equal(h.visible().x, 50); assert.equal(h.settled.length, 0);
  h.event('afterprint'); assert.equal(h.paints.at(-1).info.phase, 'cancelled'); assert.equal(h.paints.at(-1).info.progress, 0.5);
});
test('cancel preserves the legal target, and finish completes that target exactly once', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }); h.step(40); h.controller.cancel();
  assert.equal(h.controller.snapshot().get('alpha').x, 40); assert.equal(h.controller.target().get('alpha').x, 100);
  assert.equal(h.controller.isRunning(), false); assert.equal(h.settled.length, 0);
  h.controller.finish(); assert.equal(h.visible().x, 100); assert.equal(h.paints.at(-1).info.phase, 'settled');
  h.controller.finish(); assert.equal(h.settled.length, 1);
});
test('cancelled scenes export and print at the retained target, never at a hidden-label half frame', () => {
  for (const route of ['export', 'print', 'reduce']) {
    let hidden;
    const h = harness({ paint(scene, info) { hidden = ['transition', 'cancelled'].includes(info.phase); } });
    h.controller.to({ alpha: { x: 100 } }); h.step(40); h.controller.cancel(); assert.equal(hidden, true);
    if (route === 'export') assert.equal(h.controller.withStableFrame(s => s.get('alpha').x), 100);
    if (route === 'print') { h.event('beforeprint'); h.event('afterprint'); }
    if (route === 'reduce') h.reduce(true);
    assert.equal(h.visible().x, 100); assert.equal(hidden, false); assert.equal(h.controller.isRunning(), false);
  }
});
test('new to after cancellation replaces the pending target and starts from frozen geometry', () => {
  const h = harness(); h.controller.to({ alpha: { x: 100 } }); h.step(40); h.controller.cancel();
  h.controller.to({ alpha: { x: 0 } }); assert.equal(h.visible().x, 40); assert.equal(h.controller.target().get('alpha').x, 0);
  h.step(50); assert.equal(h.visible().x, 20); h.controller.cancel(); h.controller.finish(); assert.equal(h.visible().x, 0);
});
test('stable export refuses a callback-interrupted pending target rather than silently returning a half frame', () => {
  let h, second = false;
  h = harness({ onStart() { if (second) h.controller.cancel(); }, onSettled() {
    if (!second) { second = true; h.controller.to({ alpha: { x: 90 } }); }
  } });
  h.controller.to({ alpha: { x: 100 } }); h.step(40);
  let exported = false;
  assert.throws(() => h.controller.withStableFrame(() => { exported = true; }), /interrupted/);
  assert.equal(exported, false); assert.equal(h.controller.target().get('alpha').x, 90);
  h.controller.finish(); assert.equal(h.visible().x, 90);
});
