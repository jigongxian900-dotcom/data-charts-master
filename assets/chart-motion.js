/* ChartMotion 1.0.1 | optional, dependency-free scene transitions | SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ChartMotion = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function clone(value, path) {
    path = path || 'geometry';
    if (typeof value === 'number') {
      if (!Number.isFinite(value)) throw new TypeError(path + ': expected a finite number');
      return value;
    }
    if (value === null || typeof value === 'string' || typeof value === 'boolean') return value;
    if (Array.isArray(value)) {
      for (var i = 0; i < value.length; i += 1) {
        if (!Object.prototype.hasOwnProperty.call(value, i)) throw new TypeError(path + ': sparse arrays are not supported');
      }
      return value.map(function (v, index) { return clone(v, path + '[' + index + ']'); });
    }
    if (value && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null)) {
      var copy = Object.create(null);
      Object.keys(value).forEach(function (key) { copy[key] = clone(value[key], path + '.' + key); });
      return copy;
    }
    throw new TypeError(path + ': expected numbers, static strings/booleans/null, arrays or plain objects');
  }
  function scene(input) {
    var result = new Map();
    var entries;
    if (input instanceof Map) entries = input.entries();
    else if (input && (Object.getPrototypeOf(input) === Object.prototype || Object.getPrototypeOf(input) === null)) entries = Object.entries(input);
    else throw new TypeError('scene must be a Map or plain object keyed by stable string IDs');
    for (var pair of entries) {
      if (typeof pair[0] !== 'string' || !pair[0]) throw new TypeError('scene IDs must be nonempty strings');
      result.set(pair[0], clone(pair[1], pair[0]));
    }
    return result;
  }
  function equal(a, b) {
    if (a === b) return true;
    if (!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
    var ak = Object.keys(a), bk = Object.keys(b);
    return ak.length === bk.length && ak.every(function (key) { return Object.prototype.hasOwnProperty.call(b, key) && equal(a[key], b[key]); });
  }
  function equalScene(a, b) {
    return a.size === b.size && Array.from(a).every(function (pair) { return b.has(pair[0]) && equal(pair[1], b.get(pair[0])); });
  }
  function compatible(a, b, path) {
    if (typeof a === 'number' && typeof b === 'number') return;
    if (a === b) return;
    if (a && b && typeof a === 'object' && typeof b === 'object' && Array.isArray(a) === Array.isArray(b)) {
      var ak = Object.keys(a), bk = Object.keys(b);
      if (ak.length === bk.length && ak.every(function (k) { return Object.prototype.hasOwnProperty.call(b, k); })) {
        ak.forEach(function (k) { compatible(a[k], b[k], path + '.' + k); });
        return;
      }
    }
    throw new TypeError(path + ': incompatible geometry; supply interpolate or make an explicit staged transition (SVG path strings are never number-morphed)');
  }
  function interpolateNumbers(a, b, t) {
    if (typeof a === 'number' && typeof b === 'number') return a * (1 - t) + b * t;
    if (a === b) return a;
    var output = Array.isArray(a) ? [] : Object.create(null);
    Object.keys(a).forEach(function (k) { output[k] = interpolateNumbers(a[k], b[k], t); });
    return output;
  }
  function create(options) {
    options = options || {};
    if (typeof options.paint !== 'function') throw new TypeError('paint is required');
    var host = typeof window !== 'undefined' ? window : null;
    var env = options.environment || {};
    var now = env.now || function () { return typeof performance !== 'undefined' ? performance.now() : Date.now(); };
    var raf = env.requestFrame || (host && host.requestAnimationFrame ? host.requestAnimationFrame.bind(host) : function (fn) { return setTimeout(fn, 16); });
    var caf = env.cancelFrame || (host && host.cancelAnimationFrame ? host.cancelAnimationFrame.bind(host) : clearTimeout);
    var eventTarget = Object.prototype.hasOwnProperty.call(env, 'eventTarget') ? env.eventTarget : host;
    var media = Object.prototype.hasOwnProperty.call(env, 'mediaQuery') ? env.mediaQuery : (host && host.matchMedia ? host.matchMedia('(prefers-reduced-motion: reduce)') : null);
    var current = scene(options.scene || {}), destination = scene(current);
    var job = null, pending = null, frame = null, generation = 0, destroyed = false, stableDepth = 0;
    var reduced = !!(media && media.matches), lastMeta = options.meta, visiblePhase = 'settled', visibleProgress = 1;
    function alive() { if (destroyed) throw new Error('ChartMotion has been destroyed'); }
    function invalidate() {
      generation += 1;
      if (frame !== null) caf(frame);
      frame = null;
      job = null;
      return generation;
    }
    function info(phase, progress, reason, active) {
      return { phase: phase, progress: progress, reason: reason, meta: active ? active.meta : lastMeta,
        entering: active ? active.entering.slice() : [], exiting: active ? active.exiting.slice() : [] };
    }
    function paint(phase, progress, reason, active) {
      visiblePhase = phase; visibleProgress = progress;
      options.paint(scene(current), info(phase, progress, reason, active));
    }
    function settle(active, reason) {
      var token = invalidate();
      pending = null;
      current = scene(active.target);
      destination = scene(active.target);
      lastMeta = active.meta;
      paint('settled', 1, reason, active);
      if (!destroyed && token === generation && typeof options.onSettled === 'function') options.onSettled(scene(current), info('settled', 1, reason, active));
    }
    function finish(reason) {
      alive();
      if (job || pending) settle(job || pending, reason || 'finish');
      return scene(current);
    }
    function tick(token, active) {
      if (destroyed || token !== generation || job !== active) return;
      frame = null;
      try {
        var elapsed = Math.max(0, now() - active.start);
        var progress = Math.min(1, elapsed / active.duration);
        if (progress >= 1) { settle(active, 'complete'); return; }
        var eased = active.ease(progress);
        if (destroyed || generation !== token || job !== active) return;
        if (!Number.isFinite(eased)) throw new TypeError('ease must return a finite number');
        eased = Math.max(0, Math.min(1, eased));
        var next = new Map();
        active.from.forEach(function (from, id) {
          if (destroyed || generation !== token || job !== active) return;
          var value = active.interpolate ? active.interpolate(clone(from), clone(active.to.get(id)), eased, id,
            { progress: progress, meta: active.meta, entering: active.entering.includes(id), exiting: active.exiting.includes(id) }) : interpolateNumbers(from, active.to.get(id), eased);
          next.set(id, clone(value, id));
        });
        if (destroyed || generation !== token || job !== active) return;
        current = next;
        active.progress = progress;
        paint('transition', progress, 'frame', active);
        if (!destroyed && generation === token && job === active) frame = raf(function () { tick(token, active); });
      } catch (error) {
        // Never erase a replacement transition created by a reentrant author callback.
        if (generation === token) invalidate();
        throw error;
      }
    }
    function to(input, settings) {
      alive();
      settings = settings || {};
      var target = scene(input);
      var duration = settings.duration === undefined ? (options.duration === undefined ? 320 : options.duration) : settings.duration;
      if (!Number.isFinite(duration) || duration < 0) throw new RangeError('duration must be a finite nonnegative number');
      var custom = settings.interpolate || options.interpolate;
      if (custom !== undefined && typeof custom !== 'function') throw new TypeError('interpolate must be a function');
      var ease = settings.ease || options.ease || function (t) { return t; };
      if (typeof ease !== 'function') throw new TypeError('ease must be a function');
      var from = scene(current), aligned = new Map(), entering = [], exiting = [];
      var preparationGeneration = generation;
      var enter = settings.enter || options.enter, exit = settings.exit || options.exit;
      target.forEach(function (value, id) {
        if (!from.has(id)) { entering.push(id); from.set(id, enter ? clone(enter(id, clone(value)), id) : clone(value)); }
        aligned.set(id, clone(value));
      });
      Array.from(from).forEach(function (pair) {
        if (!target.has(pair[0])) {
          exiting.push(pair[0]);
          if (exit) aligned.set(pair[0], clone(exit(pair[0], clone(pair[1])), pair[0]));
          else from.delete(pair[0]); // Explicit default: membership switches immediately, never by index.
        }
      });
      if (destroyed || generation !== preparationGeneration) return api;
      if (!custom) from.forEach(function (value, id) { compatible(value, aligned.get(id), id); });
      // Validate first; an invalid request must not interrupt the current animation.
      var token = invalidate();
      destination = scene(target);
      var active = { from: from, to: aligned, target: target, duration: duration, start: now(), progress: 0, ease: ease,
        interpolate: custom, entering: entering, exiting: exiting, meta: settings.meta === undefined ? options.meta : settings.meta };
      job = active;
      pending = active;
      lastMeta = active.meta;
      try {
        if (typeof options.onStart === 'function') options.onStart(scene(current), scene(target), info('start', 0, 'to', active));
      } catch (error) {
        if (generation === token) invalidate();
        throw error;
      }
      if (destroyed || generation !== token || job !== active) return api;
      if (reduced || stableDepth || duration === 0 || equalScene(current, target)) {
        settle(active, reduced ? 'reduced-motion' : stableDepth ? 'stable-frame' : duration === 0 ? 'immediate' : 'unchanged');
        return api;
      }
      current = scene(from);
      try { paint('transition', 0, 'start', active); }
      catch (error) {
        if (generation === token) invalidate();
        throw error;
      }
      if (!destroyed && generation === token && job === active) frame = raf(function () { tick(token, active); });
      return api;
    }
    function withStableFrame(callback) {
      alive();
      if (typeof callback !== 'function') throw new TypeError('callback is required');
      stableDepth += 1;
      try {
        finish('export');
        if (job || pending) throw new Error('Stable frame was interrupted by an author callback; finish the retained target before exporting');
        return callback(scene(current));
      }
      finally { stableDepth -= 1; }
    }
    function mediaChange(event) {
      reduced = !!event.matches;
      if (!destroyed && reduced) finish('reduced-motion');
    }
    function beforePrint() { if (!destroyed) withStableFrame(function () {}); }
    function afterPrint() { if (!destroyed) paint(visiblePhase, visibleProgress, 'afterprint', job); }
    if (media) {
      if (media.addEventListener) media.addEventListener('change', mediaChange);
      else if (media.addListener) media.addListener(mediaChange);
    }
    if (eventTarget && eventTarget.addEventListener) {
      eventTarget.addEventListener('beforeprint', beforePrint);
      eventTarget.addEventListener('afterprint', afterPrint);
    }
    var api = {
      to: to, transition: to, finish: finish,
      cancel: function () {
        alive();
        var active = job;
        invalidate();
        if (active) paint('cancelled', active.progress, 'cancel', active);
        return scene(current);
      },
      snapshot: function () { return scene(current); }, target: function () { return scene(destination); },
      isRunning: function () { return !!job; }, withStableFrame: withStableFrame,
      destroy: function () {
        if (destroyed) return;
        invalidate(); pending = null; destroyed = true;
        if (media) {
          if (media.removeEventListener) media.removeEventListener('change', mediaChange);
          else if (media.removeListener) media.removeListener(mediaChange);
        }
        if (eventTarget && eventTarget.removeEventListener) {
          eventTarget.removeEventListener('beforeprint', beforePrint);
          eventTarget.removeEventListener('afterprint', afterPrint);
        }
      }
    };
    try { paint('settled', 1, 'initial', null); }
    catch (error) { api.destroy(); throw error; }
    return api;
  }
  function captureFocus(root, attribute) {
    attribute = attribute || 'data-focus-key';
    var active = root && root.ownerDocument && root.ownerDocument.activeElement;
    if (!active || !root.contains(active) || !active.hasAttribute(attribute)) return null;
    var token = { key: active.getAttribute(attribute), attribute: attribute };
    if (typeof active.selectionStart === 'number') {
      token.start = active.selectionStart; token.end = active.selectionEnd; token.direction = active.selectionDirection;
    }
    return token;
  }
  function restoreFocus(root, token) {
    if (!root || !token) return false;
    var nodes = Array.from(root.querySelectorAll('*'));
    if (root.getAttribute) nodes.unshift(root);
    var matches = nodes.filter(function (node) { return node.getAttribute(token.attribute) === token.key; });
    if (matches.length !== 1 || typeof matches[0].focus !== 'function' || matches[0].disabled) return false;
    var node = matches[0];
    node.focus({ preventScroll: true });
    if (typeof token.start === 'number' && node.setSelectionRange) {
      try { node.setSelectionRange(token.start, token.end, token.direction); } catch (_) { /* non-text controls */ }
    }
    return root.ownerDocument.activeElement === node;
  }
  function preserveFocus(root, render) {
    var token = captureFocus(root);
    var result = render();
    restoreFocus(root, token);
    return result;
  }
  return { version: '1.0.1', create: create, captureFocus: captureFocus, restoreFocus: restoreFocus, preserveFocus: preserveFocus };
});
