/* Kit Build Plus — upload loading globe
 *
 * The same node sphere as the home mark, re-used here as a loading indicator
 * with one added behaviour: a heartbeat.
 *
 * Cycle (2.0s). At beat start the spin ramps up and settles back, with real
 * acceleration at both ends rather than a step in speed. The ring beside the
 * red dot detaches at that instant and expands outward as a ripple — the
 * ripple's centre is frozen at the dot's position when the beat began, so it
 * drifts away from the turning mark instead of riding along with it. The
 * expansion starts fast and decelerates. At 0.7s into the beat a fresh ring
 * grows out of the dot's centre, restoring the mark for the next beat.
 *
 * Everything is drawn on one canvas in batched passes: the sphere is 84 nodes
 * and 140 edges, and issuing a call per element would make the heartbeat
 * itself stutter.
 */

(function () {
  'use strict';

  var canvas = document.getElementById('load-globe');
  if (!canvas) return;

  var ctx = canvas.getContext('2d');
  if (!ctx) return;

  var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ── Geometry ─────────────────────────────────────────────────────── */

  var NODES = 84;
  var FOCAL = 3.4;
  var TILT = -0.34;

  var nodes = [];
  var edges = [];
  var maxHop = 0;

  function dist3(p, q) {
    var dx = p.x - q.x, dy = p.y - q.y, dz = p.z - q.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  function buildSphere() {
    nodes = [];
    edges = [];
    maxHop = 0;

    var golden = Math.PI * (3 - Math.sqrt(5));

    for (var i = 0; i < NODES; i++) {
      var y = 1 - (i / (NODES - 1)) * 2;
      var radius = Math.sqrt(Math.max(0, 1 - y * y));
      var theta = golden * i;
      nodes.push({
        x: Math.cos(theta) * radius,
        y: y,
        z: Math.sin(theta) * radius,
        hop: -1,
        alpha: 1,
        scale: 1
      });
    }

    nodes[0].x = 0.46;
    nodes[0].y = 0.12;
    nodes[0].z = 0.88;

    var seen = Object.create(null);

    for (var a = 0; a < NODES; a++) {
      var order = [];
      for (var b = 0; b < NODES; b++) {
        if (a === b) continue;
        order.push({ i: b, d: dist3(nodes[a], nodes[b]) });
      }
      order.sort(function (m, n) { return m.d - n.d; });

      var want = a === 0 ? 7 : 3;
      for (var k = 0; k < want && k < order.length; k++) {
        var j = order[k].i;
        var key = a < j ? a + ':' + j : j + ':' + a;
        if (seen[key]) continue;
        seen[key] = true;
        edges.push({ a: a, b: j, hop: 0, alpha: 1 });
      }
    }

    nodes[0].hop = 0;
    var queue = [0];
    while (queue.length) {
      var cur = queue.shift();
      for (var e = 0; e < edges.length; e++) {
        var edge = edges[e];
        var next = -1;
        if (edge.a === cur) next = edge.b;
        else if (edge.b === cur) next = edge.a;
        if (next < 0) continue;
        if (nodes[next].hop !== -1) continue;
        nodes[next].hop = nodes[cur].hop + 1;
        queue.push(next);
      }
    }
    for (var u = 0; u < NODES; u++) {
      if (nodes[u].hop === -1) nodes[u].hop = 0;
      if (nodes[u].hop > maxHop) maxHop = nodes[u].hop;
    }
    for (var q = 0; q < edges.length; q++) {
      edges[q].hop = Math.max(nodes[edges[q].a].hop, nodes[edges[q].b].hop);
    }
  }

  /* ── Projection ───────────────────────────────────────────────────── */

  var rot = 0.4;
  var BASE_SPIN = 0.085;          /* rad/s — the home mark's resting speed */
  var PULSE_SPIN = 2.6;           /* extra turns' worth of speed at the peak */

  var cosTilt = Math.cos(TILT), sinTilt = Math.sin(TILT);
  var cosSpin = 1, sinSpin = 0;

  var projX = new Float32Array(NODES);
  var projY = new Float32Array(NODES);
  var projZ = new Float32Array(NODES);
  var projP = new Float32Array(NODES);

  function projectAll() {
    cosSpin = Math.cos(rot);
    sinSpin = Math.sin(rot);
    for (var i = 0; i < NODES; i++) {
      var node = nodes[i];
      var y1 = node.y * cosTilt - node.z * sinTilt;
      var z1 = node.y * sinTilt + node.z * cosTilt;
      var x2 = node.x * cosSpin + z1 * sinSpin;
      var z2 = -node.x * sinSpin + z1 * cosSpin;
      var persp = FOCAL / Math.max(0.55, FOCAL - z2);
      projX[i] = x2 * persp;
      projY[i] = y1 * persp;
      projZ[i] = z2;
      projP[i] = persp;
    }
  }

  /* ── Theme ────────────────────────────────────────────────────────── */

  var theme = { node: '240,240,240', red: '239,68,68', link: '240,240,240' };

  function hexToRgb(hex) {
    var m = /^#([0-9a-f]{6})$/i.exec(hex);
    if (!m) return null;
    var n = parseInt(m[1], 16);
    return ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255);
  }

  function readTheme() {
    var styles = getComputedStyle(document.documentElement);
    theme.node = hexToRgb(styles.getPropertyValue('--fg').trim()) || '240,240,240';
    theme.red = hexToRgb(styles.getPropertyValue('--node-red').trim()) || '239,68,68';
    var dark = document.documentElement.getAttribute('data-theme') !== 'light';
    theme.link = dark ? '240,240,240' : '15,15,16';
  }

  /* ── Sizing ───────────────────────────────────────────────────────── */

  var cssW = 0, cssH = 0, unit = 0, dpr = 1;

  function resize() {
    var rect = canvas.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) return;

    var nextDpr = Math.min(window.devicePixelRatio || 1, 2);
    var nextW = Math.round(rect.width);
    var nextH = Math.round(rect.height);

    if (nextW === Math.round(cssW) && nextH === Math.round(cssH) && nextDpr === dpr) {
      return;
    }

    dpr = nextDpr;
    cssW = rect.width;
    cssH = rect.height;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    /* The mark occupies a smaller share of its box than on the home hero: the
       ripple runs outward from an off-centre dot and needs room before the
       canvas edge, or it is cut off mid-flight. */
    unit = Math.min(cssW, cssH) * 0.30;
  }

  /* ── Heartbeat ────────────────────────────────────────────────────── */

  var PERIOD = 2000;        /* ms between beats */
  var BEAT_MS = 1000;       /* how long one beat lasts */
  var RING_DELAY = 700;     /* the fresh ring starts 0.7s into the beat */

  var beatStarted = 0;      /* timestamp of the current beat, 0 when idle */
  var lastBeatIndex = -1;

  /* the ripple owns the dot's position from the moment the beat began */
  var ripple = { x: 0, y: 0, active: false, born: 0, baseR: 0 };

  /* smooth acceleration in and out: zero slope at both ends, peak in the
     middle. A sine squared bump is exactly that, and cheaper than a bezier. */
  function bump(u) {
    if (u <= 0 || u >= 1) return 0;
    var s = Math.sin(Math.PI * u);
    return s * s;
  }

  /* expanding with deceleration: fast at the start, easing to a stop */
  function easeOutCubic(u) {
    var inv = 1 - u;
    return 1 - inv * inv * inv;
  }

  /* ── Draw ─────────────────────────────────────────────────────────── */

  var BUCKETS = 12;
  var edgeBuckets = new Int32Array(0);
  var nodeBuckets = new Int32Array(NODES);
  var edgeStyle = new Array(BUCKETS);
  var nodeStyle = new Array(BUCKETS);

  function quantise(v) {
    var i = (v * BUCKETS) | 0;
    return i < 0 ? 0 : i >= BUCKETS ? BUCKETS - 1 : i;
  }

  function bucketAlpha(i) {
    return ((i + 0.5) / BUCKETS).toFixed(3);
  }

  function ensureEdgeBuffers() {
    if (edgeBuckets.length !== edges.length) {
      edgeBuckets = new Int32Array(edges.length);
    }
  }

  function paint(now) {
    if (!cssW) return;
    ctx.clearRect(0, 0, cssW, cssH);

    var cx = cssW / 2;
    var cy = cssH / 2;

    projectAll();
    ensureEdgeBuffers();

    var total = edges.length;
    for (var b = 0; b < BUCKETS; b++) {
      edgeStyle[b] = 'rgba(' + theme.link + ',' + bucketAlpha(b) + ')';
    }

    for (var e = 0; e < total; e++) {
      var depthAvg = (projZ[edges[e].a] + projZ[edges[e].b]) * 0.5;
      var fade = 0.30 + Math.max(0, depthAvg) * 0.42;
      edgeBuckets[e] = quantise(fade);
    }

    for (var k = 0; k < BUCKETS; k++) {
      var drew = false;
      ctx.beginPath();
      for (var j = 0; j < total; j++) {
        if (edgeBuckets[j] !== k) continue;
        var eg = edges[j];
        ctx.moveTo(cx + projX[eg.a] * unit, cy + projY[eg.a] * unit);
        ctx.lineTo(cx + projX[eg.b] * unit, cy + projY[eg.b] * unit);
        drew = true;
      }
      if (!drew) continue;
      ctx.strokeStyle = edgeStyle[k];
      ctx.lineWidth = 0.85;
      ctx.stroke();
    }

    for (var c = 0; c < BUCKETS; c++) {
      nodeStyle[c] = 'rgba(' + theme.node + ',' + bucketAlpha(c) + ')';
    }
    for (var n = 0; n < NODES; n++) {
      nodeBuckets[n] = quantise(0.42 + Math.max(0, projZ[n]) * 0.58);
    }
    for (var m = 0; m < BUCKETS; m++) {
      var any = false;
      ctx.beginPath();
      for (var q = 1; q < NODES; q++) {
        if (nodeBuckets[q] !== m) continue;
        var r = 2.15 * projP[q];
        var nx = cx + projX[q] * unit;
        var ny = cy + projY[q] * unit;
        ctx.moveTo(nx + Math.max(0.7, r), ny);
        ctx.arc(nx, ny, Math.max(0.7, r), 0, Math.PI * 2);
        any = true;
      }
      if (!any) continue;
      ctx.fillStyle = nodeStyle[m];
      ctx.fill();
    }

    /* the origin: dot, lifetime ring, ripple, regrowth */
    var ox = cx + projX[0] * unit;
    var oy = cy + projY[0] * unit;
    var oDepth = 0.42 + Math.max(0, projZ[0]) * 0.58;
    var oR = Math.max(0.7, 4.6 * projP[0]);
    var homeR = oR * 2.7;

    var beatT = beatStarted ? now - beatStarted : -1;
    var inBeat = beatT >= 0 && beatT <= BEAT_MS;

    /* the home ring is consumed by the ripple at beat start, then regrows from
       the dot's centre at 0.7s — so it is absent (or growing) for part of the
       cycle and never pops back at full size */
    var ringScale = 1;
    if (inBeat) {
      if (beatT < RING_DELAY) {
        ringScale = 0;
      } else {
        var grow = (beatT - RING_DELAY) / (BEAT_MS - RING_DELAY);
        ringScale = easeOutCubic(Math.min(1, grow));
      }
    }

    if (ringScale > 0.001) {
      ctx.beginPath();
      ctx.arc(ox, oy, Math.max(0.1, homeR * ringScale), 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(' + theme.red + ',' + (0.42 * oDepth * ringScale).toFixed(3) + ')';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    /* the ripple: centre frozen at the dot's place when the beat began */
    if (ripple.active) {
      var rT = (now - ripple.born) / BEAT_MS;
      /* A stale ripple can be painted against a clock that has gone back to
         zero — `start()` in the reduced-motion branch, a resize after the view
         closed, a theme repaint while stopped. A negative rT fed a negative
         radius into `ctx.arc`, which throws; and the throw landed before the
         ticker below was installed, so the status line stopped rotating for
         the rest of the session. */
      if (rT < 0 || rT >= 1) {
        ripple.active = false;
      } else {
        /* The ripple leaves the ring rather than replacing it: it starts at
           the ring's own peak alpha and weight (0.42, 2px) and falls away
           from there. It used to start at 0.5 with the trailing front drawn
           on top at the same radius, which put a frame ~2.4x brighter than
           the resting ring on screen at every single beat. */
        var rr = ripple.baseR + (homeR * 4.4) * easeOutCubic(rT);
        var ra = (1 - rT) * (1 - rT) * 0.42 * oDepth;
        ctx.beginPath();
        ctx.arc(ripple.x, ripple.y, Math.max(0.1, rr), 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(' + theme.red + ',' + ra.toFixed(3) + ')';
        ctx.lineWidth = 2;
        ctx.stroke();

        /* a second, fainter front a little behind it gives the ripple body
           instead of a single hairline — but only once it has somewhere to be,
           or the two coincide on the first frame */
        var rT2 = rT - 0.12;
        if (rT2 > 0) {
          var rr2 = ripple.baseR + (homeR * 4.4) * easeOutCubic(rT2);
          ctx.beginPath();
          ctx.arc(ripple.x, ripple.y, Math.max(0.1, rr2), 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(' + theme.red + ',' + (ra * 0.45).toFixed(3) + ')';
          ctx.lineWidth = 1.4;
          ctx.stroke();
        }
      }
    }

    ctx.beginPath();
    ctx.arc(ox, oy, oR, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(' + theme.red + ',1)';
    ctx.fill();
  }

  /* ── Loop ─────────────────────────────────────────────────────────── */

  var raf = 0;
  var lastFrame = 0;
  var started = 0;
  var running = false;

  function step(now) {
    if (!started) { started = now; lastFrame = now; }
    var dt = lastFrame ? Math.min(64, now - lastFrame) : 16;
    lastFrame = now;

    /* beat index derives from the clock, so a dropped frame cannot shift the
       rhythm the way an accumulating timer would */
    var elapsed = now - started;
    var index = Math.floor(elapsed / PERIOD);

    if (index !== lastBeatIndex) {
      lastBeatIndex = index;
      beatStarted = now;
      announce(index);

      /* freeze the dot's position at this instant — the ripple must not follow
         the mark as it keeps turning */
      if (cssW) {
        var cx = cssW / 2, cy = cssH / 2;
        ripple.x = cx + projX[0] * unit;
        ripple.y = cy + projY[0] * unit;
        ripple.born = now;
        ripple.baseR = Math.max(0.7, 4.6 * projP[0]) * 2.7;
        ripple.active = !motionQuery.matches;
      }
    }

    /* speed: resting spin plus a smooth bump while the beat is live */
    var beatT = beatStarted ? now - beatStarted : BEAT_MS + 1;
    var boost = 0;
    if (beatT >= 0 && beatT <= BEAT_MS) {
      boost = bump(beatT / BEAT_MS) * PULSE_SPIN;
    }
    rot += ((BASE_SPIN + boost) * dt) / 1000;
    if (rot > Math.PI * 2) rot -= Math.PI * 2;

    paint(now);
    raf = requestAnimationFrame(step);
  }

  /* Announced once per beat so the status line under the mark changes on the
     same impulse the ripple leaves on. Kept separate from drawing: the copy has
     to keep rotating even when reduced motion stops the canvas. */
  var onBeat = null;

  function announce(index) {
    if (typeof onBeat === 'function') onBeat(index);
  }

  function start() {
    if (running) return;
    running = true;
    readTheme();
    resize();

    if (motionQuery.matches) {
      /* still mark: no beat, no ripple, no spin. The status line is text, not
         motion, so it keeps rotating — otherwise the screen looks frozen and
         the student cannot tell the upload is still running. */
      ripple.active = false;
      paint(0);
      stopTicker();
      tickIndex = 0;
      ticker = window.setInterval(function () {
        tickIndex += 1;
        announce(tickIndex);
      }, PERIOD);
      return;
    }

    started = 0;
    lastFrame = 0;
    beatStarted = 0;
    /* nothing is in flight on a fresh start, so no stale ripple can be painted
       against the new clock */
    ripple.active = false;
    /* index 0 is the tick the loop boots on, not a beat: seeding the counter
       with it puts the first real beat one full period later */
    lastBeatIndex = 0;
    raf = requestAnimationFrame(step);
  }

  var ticker = 0;
  var tickIndex = 0;

  function stopTicker() {
    if (ticker) window.clearInterval(ticker);
    ticker = 0;
  }

  function stop() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    running = false;
    /* the mark is off screen; a ripple left mid-flight would be painted
       against a cold clock by the next resize or repaint */
    ripple.active = false;
    stopTicker();
  }

  buildSphere();
  readTheme();
  resize();

  window.addEventListener('resize', function () {
    if (!cssW) return;
    resize();
    if (!running || motionQuery.matches) paint(0);
  });

  if (motionQuery.addEventListener) {
    motionQuery.addEventListener('change', function () {
      stop();
      start();
    });
  }

  window.KBPLoadGlobe = {
    start: start,
    stop: stop,
    /* the copy layer subscribes here so text and ripple stay on one clock */
    onBeat: function (fn) { onBeat = fn; },
    repaint: function () {
      readTheme();
      if (!running) paint(0);
    }
  };
})();
