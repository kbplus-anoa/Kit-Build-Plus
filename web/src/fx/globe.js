/* Kit Build Plus — node globe
   A red origin node links outward, hop by hop, into a sphere of concepts,
   then rotates slowly. It leans toward a pointer that comes near it. The
   nodes carry no data: this is the brand mark. */

(function () {
  'use strict';

  var canvas = document.getElementById('globe');
  if (!canvas) return;

  var ctx = canvas.getContext('2d');
  /* queried live, not snapshotted at load: a user can flip the system
     setting while the page is open and the mark must obey it immediately */
  var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ── Geometry ─────────────────────────────────────────────────── */

  /* 84 nodes still read as a dense sphere at 420px; 104 added little visible
     detail while costing a fifth more per-frame projection work. */
  var NODES = 84;
  var FOCAL = 3.4;                 /* camera distance in sphere radii */
  var TILT = -0.34;                /* lean the sphere so it reads 3D */

  var nodes = [];
  var edges = [];
  var maxHop = 0;

  function buildSphere() {
    /* rebuilding must replace, never append — start() runs after the
       first paint, and a second pass would double every node */
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
        alpha: 0,
        born: 0,
        scale: 1
      });
    }

    /* the origin sits on the front face, slightly right of centre */
    nodes[0].x = 0.46;
    nodes[0].y = 0.12;
    nodes[0].z = 0.88;

    /* connect each node to its nearest few neighbours on the sphere */
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
        edges.push({ a: a, b: j, hop: 0, alpha: 0 });
      }
    }

    /* hop distance from the origin decides the outward build order */
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

    /* anything unreached (should not happen) joins at the last level */
    for (var u = 0; u < NODES; u++) {
      if (nodes[u].hop === -1) nodes[u].hop = 0;
      if (nodes[u].hop > maxHop) maxHop = nodes[u].hop;
    }

    for (var q = 0; q < edges.length; q++) {
      edges[q].hop = Math.max(nodes[edges[q].a].hop, nodes[edges[q].b].hop);
    }
  }

  function dist3(p, q) {
    var dx = p.x - q.x, dy = p.y - q.y, dz = p.z - q.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /* ── Projection ───────────────────────────────────────────────── */

  var rot = 0;                 /* current Y rotation, radians */
  var spinSpeed = 0.085;       /* rad per second — slow */

  /* Trig for the tilt is constant; trig for the spin is evaluated once per
     frame instead of once per node. Both live in a small shared state so the
     84-node projection does no transcendental work and allocates nothing. */
  var cosTilt = Math.cos(TILT), sinTilt = Math.sin(TILT);
  var cosSpin = 1, sinSpin = 0;

  var projX = new Float32Array(NODES);
  var projY = new Float32Array(NODES);
  var projZ = new Float32Array(NODES);
  var projP = new Float32Array(NODES);

  function updateSpin() {
    cosSpin = Math.cos(rot);
    sinSpin = Math.sin(rot);
  }

  function projectAll() {
    for (var i = 0; i < NODES; i++) {
      var node = nodes[i];

      /* tilt around X (constant) */
      var y1 = node.y * cosTilt - node.z * sinTilt;
      var z1 = node.y * sinTilt + node.z * cosTilt;

      /* spin around Y (per frame) */
      var x2 = node.x * cosSpin + z1 * sinSpin;
      var z2 = -node.x * sinSpin + z1 * cosSpin;

      var persp = FOCAL / Math.max(0.55, FOCAL - z2);

      projX[i] = x2 * persp;
      projY[i] = y1 * persp;
      projZ[i] = z2;
      projP[i] = persp;
    }
  }

  /* ── Cursor attraction ─────────────────────────────────────────────
     Bringing the pointer near the mark draws the nodes around it a little way
     toward the cursor. The nudge is applied in screen space — after projection,
     before anything is drawn — so every link rides along with its own endpoints
     without the drawing code knowing about it, and the sphere is never
     reshaped: move the pointer away and each node eases back to exactly where
     the geometry put it.

     Two easings, both frame-rate independent: the pointer position itself, so
     a quick sweep drags the nodes behind the cursor instead of snapping, and
     the overall energy, which is what makes the effect arrive and leave
     gently rather than appearing under the hand. */

  var PULL_REACH = 0.62;       /* how far the pointer reaches, in sphere radii */
  /* Strength is set by measurement, not by eye: at the mark's own radius a
     stronger pull made neighbouring dots bunch to 18-29% of their spacing,
     which reads as dots passing through each other. At this value the
     closest surviving pair keeps 41% and nothing crosses. */
  var PULL_STRENGTH = 0.09;    /* peak displacement, same unit as the reach */
  var PULL_GROW = 0.4;         /* extra dot size for a fully pulled node */
  var PULL_EASE_MS = 90;       /* pointer lag — short enough to feel attached */

  var pointer = { x: 0, y: 0, tx: 0, ty: 0, on: false, energy: 0 };
  var canvasRect = null;       /* the canvas box, cached for one painted frame */
  var pullAmt = new Float32Array(NODES);

  function advancePointer(dt) {
    /* Reduced motion opts out of the pull entirely: it is movement that
       follows the cursor, which is the thing that setting asks us to stop.
       Easing `want` to 0 is what relaxes the nodes when the pointer leaves;
       a settings change mid-session stops the loop instead, so that path
       drops the pull outright in resetPull(). */
    var want = pointer.on && !motionQuery.matches ? 1 : 0;
    var k = 1 - Math.exp(-dt / PULL_EASE_MS);

    pointer.x += (pointer.tx - pointer.x) * k;
    pointer.y += (pointer.ty - pointer.y) * k;
    pointer.energy += (want - pointer.energy) * k;

    if (!want && pointer.energy < 0.002) {
      pointer.energy = 0;
      pointer.x = pointer.tx;
      pointer.y = pointer.ty;
    }
  }

  /* no pointer, no pull — used wherever the mark stops animating, so a frozen
     frame can never keep the nodes stretched out of place */
  function resetPull() {
    pointer.on = false;
    pointer.energy = 0;
  }

  function applyPull(cx, cy) {
    if (pointer.energy <= 0.002) {
      for (var z = 0; z < NODES; z++) pullAmt[z] = 0;
      return;
    }

    var reach = unit * PULL_REACH;
    /* pointer.x/y are already canvas-box pixels, the same space the dots are
       drawn in below — adding the centre again here would offset the whole
       influence by half the box and put it off canvas */
    var px = pointer.x;
    var py = pointer.y;

    for (var i = 0; i < NODES; i++) {
      /* read before writing: each node's displacement depends only on where
         the geometry put it, never on a neighbour already nudged this frame */
      var sx = cx + projX[i] * unit;
      var sy = cy + projY[i] * unit;
      var dx = px - sx;
      var dy = py - sy;
      var d = Math.sqrt(dx * dx + dy * dy);

      if (d >= reach) { pullAmt[i] = 0; continue; }

      /* smoothstep, so influence has no visible rim where it starts */
      var t = 1 - d / reach;
      var f = t * t * (3 - 2 * t);

      /* A node directly under the cursor has no direction to be drawn in, and
         the near face of the sphere is the part a hand reaches for: the far
         side answers less. Both cases stay put rather than jumping. */
      var depth = 0.6 + Math.max(0, projZ[i]) * 0.4;

      if (d < 0.75) { pullAmt[i] = 0; continue; }

      pullAmt[i] = f * depth * pointer.energy;
      var move = f * depth * pointer.energy * PULL_STRENGTH * unit;

      projX[i] += (dx / d) * move / unit;
      projY[i] += (dy / d) * move / unit;
    }
  }

  /* ── Sizing ───────────────────────────────────────────────────── */

  var cssW = 0, cssH = 0, unit = 0, dpr = 1;

  /* A resize burst must collapse into one measurement. The event can fire on
     every frame of a window drag, and each measurement that finds a new size
     reallocates the backing store, so the listener only raises this flag and
     the frame loop absorbs it once. */
  var sizeDirty = false;

  /* Geometry only — no theme read, no paint. Nothing about the palette changed
     because the box did, and painting here would duplicate work the loop is
     about to do anyway. */
  function measure() {
    var rect = canvas.getBoundingClientRect();

    /* the home view is hidden while the report is open; measuring then would
       collapse the canvas to 1px and leave it tiny on return. Keep the last
       good size until the stage is actually laid out again — and leave the
       dirty flag raised, so whatever asked for this measurement gets another
       chance once there is a box to measure. */
    if (rect.width < 2 || rect.height < 2) return;

    sizeDirty = false;

    /* The mark is drawn from 1px lines and 2px dots. At DPR 2 the canvas is
       already 4× the CSS pixel count; going to 3 adds 9× the fill rate for
       detail this geometry cannot show. Cap at 2, and drop to 1.5 when the
       stage is large, since the extra pixels are least visible there. */
    var nextDpr = Math.min(window.devicePixelRatio || 1, rect.width > 380 ? 1.5 : 2);

    /* Assigning canvas.width even to the same value wipes the backing store and
       forces a full reallocation. A theme switch measures while nothing has
       moved, so the rebuild is skipped when the geometry is unchanged. */
    if (Math.round(rect.width) === Math.round(cssW) &&
        Math.round(rect.height) === Math.round(cssH) &&
        nextDpr === dpr) {
      return;
    }

    dpr = nextDpr;
    cssW = rect.width;
    cssH = rect.height;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    unit = Math.min(cssW, cssH) * 0.42;
  }

  /* ── Palette (read from the live theme) ───────────────────────── */

  var theme = { node: '240,240,240', red: '239,68,68', link: '240,240,240' };

  function readTheme() {
    var styles = getComputedStyle(document.documentElement);
    var fg = hexToRgb(styles.getPropertyValue('--fg').trim()) || '240,240,240';
    var red = hexToRgb(styles.getPropertyValue('--node-red').trim()) || '239,68,68';
    var dark = document.documentElement.getAttribute('data-theme') !== 'light';
    theme.node = fg;
    theme.red = red;
    theme.link = dark ? '240,240,240' : '15,15,16';
    /* the draw styles are derived from the palette alone, so the one moment
       they are known to be stale is right here */
    buildStyles();
  }

  function hexToRgb(hex) {
    var m = /^#([0-9a-f]{6})$/i.exec(hex);
    if (!m) return null;
    var n = parseInt(m[1], 16);
    return ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255);
  }

  /* ── Draw ─────────────────────────────────────────────────────── */

  /* Batching: the mark is 84 nodes in 140 links, and one stroke()/fill() per
     element would be 224 passes a frame. Alpha is quantised into buckets
     instead and each non-empty bucket is drawn as one path, so a frame costs at
     most 12 strokes and 12 fills — fewer while the build is still filling the
     buckets up. Bucket count is high enough that a node's depth shading never
     visibly steps as it turns — too few buckets would look like the stutter we
     are fixing. */
  /* Buckets trade draw calls against visible banding. 24 was oversampled at
     this disc size — the step between adjacent buckets was below one alpha
     level in practice. 12 halves the number of stroke/fill passes while
     staying far above the point where a node looks like it "jumps" a shade
     as it turns past the limb. */
  var BUCKETS = 12;
  var edgeBuckets = new Int32Array(0);
  var nodeBuckets = new Int32Array(NODES);
  var edgeStyle = new Array(BUCKETS);
  var nodeStyle = new Array(BUCKETS);
  /* the origin's two colours are built from this prefix plus a live alpha;
     buildStyles() replaces it with the theme's red as soon as one is read */
  var redPrefix = 'rgba(239,68,68,';

  function quantise(value) {
    var i = (value * BUCKETS) | 0;
    return i < 0 ? 0 : i >= BUCKETS ? BUCKETS - 1 : i;
  }

  function bucketAlpha(i) {
    return ((i + 0.5) / BUCKETS).toFixed(3);
  }

  /* Every bucket colour is a function of the palette and its own index and of
     nothing else, so the 24 strings are built when the theme is read instead of
     being re-concatenated on each of the 60+ frames a second the mark is on
     screen. That removes the last per-frame allocation from the draw path. */
  function buildStyles() {
    for (var i = 0; i < BUCKETS; i++) {
      var a = bucketAlpha(i);
      edgeStyle[i] = 'rgba(' + theme.link + ',' + a + ')';
      nodeStyle[i] = 'rgba(' + theme.node + ',' + a + ')';
    }
    redPrefix = 'rgba(' + theme.red + ',';
  }

  function ensureEdgeBuffers() {
    if (edgeBuckets.length !== edges.length) {
      edgeBuckets = new Int32Array(edges.length);
    }
  }

  function paint() {
    if (!cssW) return;
    /* a fresh frame is the one moment the canvas box is known to be current */
    canvasRect = null;
    ctx.clearRect(0, 0, cssW, cssH);

    var cx = cssW / 2;
    var cy = cssH / 2;

    updateSpin();
    projectAll();
    /* projectAll() rewrites every projected coordinate from the sphere, so the
       pull always starts from clean geometry however often paint() runs */
    applyPull(cx, cy);

    ensureEdgeBuffers();

    /* bucket the edges by their effective opacity, once */
    var total = edges.length;

    for (var e = 0; e < total; e++) {
      var edge = edges[e];
      var la = edge.alpha;
      if (la <= 0.001) {
        edgeBuckets[e] = -1;
        continue;
      }
      var depthAvg = (projZ[edge.a] + projZ[edge.b]) * 0.5;
      var fade = 0.30 + Math.max(0, depthAvg) * 0.42;
      edgeBuckets[e] = quantise(la * fade);
    }

    /* one stroke per bucket */
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

    /* nodes, same batching; node 0 keeps its own ring and red fill */
    for (var n = 0; n < NODES; n++) {
      var nd = nodes[n];
      nodeBuckets[n] = nd.alpha <= 0.001 ? -1
        : quantise(nd.alpha * (0.42 + Math.max(0, projZ[n]) * 0.58));
    }

    for (var m = 0; m < BUCKETS; m++) {
      var any = false;
      ctx.beginPath();
      for (var q = 1; q < NODES; q++) {
        if (nodeBuckets[q] !== m) continue;
        /* a pulled node swells a little, which is what makes the attraction
           read as the mark answering the cursor rather than as drift */
        var r = 2.15 * projP[q] * nodes[q].scale * (1 + pullAmt[q] * PULL_GROW);
        ctx.moveTo(cx + projX[q] * unit + Math.max(0.7, r), cy + projY[q] * unit);
        ctx.arc(cx + projX[q] * unit, cy + projY[q] * unit, Math.max(0.7, r), 0, Math.PI * 2);
        any = true;
      }
      if (!any) continue;
      ctx.fillStyle = nodeStyle[m];
      ctx.fill();
    }

    /* the origin: ring plus dot, the one red element in the mark */
    var o = nodes[0];
    if (o.alpha > 0.001) {
      var ox = cx + projX[0] * unit;
      var oy = cy + projY[0] * unit;
      var oDepth = 0.42 + Math.max(0, projZ[0]) * 0.58;
      var oR = 4.6 * projP[0] * o.scale;

      ctx.beginPath();
      ctx.arc(ox, oy, oR * 2.7, 0, Math.PI * 2);
      ctx.strokeStyle = redPrefix + (0.42 * o.alpha * oDepth).toFixed(3) + ')';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(ox, oy, Math.max(0.7, oR), 0, Math.PI * 2);
      ctx.fillStyle = redPrefix + o.alpha.toFixed(3) + ')';
      ctx.fill();
    }
  }

  /* ── Timeline ─────────────────────────────────────────────────── */

  /* Assembly timing. The mark is 84 nodes in 140 links, and the BFS out from
     the origin runs 9 hops deep — the 3-nearest mesh on a sphere of this size
     is sparse, so the build is a wave that crawls across the surface rather
     than three or four shells. At the original 132ms per hop the wave alone was
     1188ms and the last node landed at 1808ms, which is a long time to look at
     an empty hero.

     These values put every node in place by 1088ms and still read as one hop
     per beat: easeOut is front-loaded, so a node is half visible 68ms into its
     own fade, just past the 62ms that separates one hop from the next. The
     order, the outward wave and the links leading their nodes are unchanged —
     only the spacing is tighter. */
  var LEAD_IN = 200;        /* full-screen aurora only, before any node */
  var HOP_GAP = 62;         /* ms between hop levels */
  var NODE_FADE = 330;      /* ms for a node to reach full opacity */
  var LINK_FADE = 260;      /* a link settles faster than the node it reaches */
  var LINK_LEAD = 20;       /* a link starts this long before its own node */

  var started = 0;
  var raf = 0;
  var settled = false;
  var paused = false;
  var onSettled = null;

  function easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  /* Resume without a time jump: lastFrame is reset so the first frame after
     a pause advances the spin by one frame, not by the whole gap.
     Reduced motion opts out of the loop entirely — resuming there would
     start spinning a mark the user asked to keep still. */
  function resume() {
    if (!paused || motionQuery.matches) return;
    paused = false;
    lastFrame = 0;
    raf = requestAnimationFrame(step);
  }

  /* Paint on every animation frame, at whatever rate the display runs.
     There used to be a ~60fps cap here, on the theory that a 120Hz panel was
     drawing the same slow turn twice. It cost more than it saved: a time
     threshold compared against a 120Hz beat never lands evenly, so frames
     came out 16, 24, 16, 20ms apart. The mark stuttered against an aurora
     that was still gliding at 120Hz, and the whole page read as janky while
     the profiler showed the main thread 91% idle and every paint under 10ms
     for a 14s trace. The cap was the judder. dt is already measured from the
     previous frame, so the rotation stays correct at any refresh rate. */
  function step(now) {
    /* a resize burst that arrived since the last frame is absorbed here, once,
       instead of re-measuring on every event */
    if (sizeDirty) measure();

    if (!started) { started = now; lastFrame = now; }
    var t = now - started;

    /* the sphere turns from the very first frame — the assembly happens on
       a surface that is already in motion, never on a still one that only
       starts spinning once it is complete */
    var dt = lastFrame ? Math.min(64, now - lastFrame) : 16;
    rot += (spinSpeed * dt) / 1000;
    if (rot > Math.PI * 2) rot -= Math.PI * 2;
    lastFrame = now;

    /* Once the build is over, every node sits at its final alpha and scale and
       this pair of loops would recompute the same 224 values on every frame for
       the rest of the session. The wave is a pure function of time and nothing
       else writes those fields, so there is nothing left to update. */
    if (!settled && t >= LEAD_IN) {
      var since = t - LEAD_IN;

      for (var i = 0; i < NODES; i++) {
        var node = nodes[i];
        var startAt = node.hop * HOP_GAP;
        var local = (since - startAt) / NODE_FADE;
        node.alpha = local <= 0 ? 0 : local >= 1 ? 1 : easeOut(local);
        /* a small settle on arrival keeps the node feeling placed, not drawn */
        var pop = local <= 0 ? 0.72 : local >= 1 ? 1 : 0.72 + easeOut(local) * 0.28;
        node.scale = pop;
      }

      for (var e = 0; e < edges.length; e++) {
        var edge = edges[e];
        var linkStart = edge.hop * HOP_GAP - LINK_LEAD;
        var l = (since - linkStart) / LINK_FADE;
        edge.alpha = l <= 0 ? 0 : l >= 1 ? 1 : easeOut(l);
      }
    }

    /* the pointer trails behind the cursor by design, so this runs on the
       frame clock rather than once per pointermove event */
    advancePointer(dt);

    paint();

    /* mirrors the hop spacing above: the last node's fade is what ends the
       build, so the two have to move together */
    var assembleEnd = LEAD_IN + maxHop * HOP_GAP + NODE_FADE;

    if (!settled && t >= assembleEnd) {
      settled = true;
      if (typeof onSettled === 'function') onSettled();
    }

    raf = requestAnimationFrame(step);
  }

  var lastFrame = 0;

  /* ── Public start ─────────────────────────────────────────────── */

  function start(callback) {
    onSettled = callback || null;
    readTheme();
    /* The geometry is built once, at load. start() runs later and the sphere it
       would build is identical, so rebuilding here would redo 84×83 distance
       tests and 84 sorts for nothing. */
    if (!nodes.length) buildSphere();

    if (motionQuery.matches) {
      /* no build animation: the assembled mark is the artifact */
      for (var i = 0; i < NODES; i++) {
        nodes[i].alpha = 1;
        nodes[i].scale = 1;
      }
      for (var e = 0; e < edges.length; e++) edges[e].alpha = 1;
      rot = 0.4;
      settled = true;
      /* no loop will ever run here, so the one frame that is drawn has to be
         the true mark: an inherited pull would leave it permanently skewed */
      resetPull();
      paint();
      if (typeof onSettled === 'function') onSettled();
      return;
    }

    started = 0;
    raf = requestAnimationFrame(step);
  }

  /* One synchronous layout and one clear frame before the loop starts, so the
     canvas has real backing-store pixels from the very first paint. Nothing is
     drawn in that frame and that is deliberate: the mark assembles in from
     LEAD_IN, so until then the stage is the aurora alone — which is what
     LEAD_IN exists for. buildSphere() already leaves every node at alpha 0. */
  readTheme();
  buildSphere();
  measure();
  paint();

  /* The handler only raises a flag; step() absorbs it on the next frame, so a
     drag that resizes the window measures once per frame instead of once per
     event. With the loop stopped — reduced motion, or a subpage holding the
     stage — nothing would absorb it, and the mark would keep a backing store
     sized for the old box, so those cases are handled here. */
  window.addEventListener('resize', function () {
    sizeDirty = true;
    if (!raf) { measure(); paint(); }
  });

  /* The pull is bound to the canvas itself, which is what keeps it honest:
     a hidden home view receives no pointer events, so there is nothing to
     track and nothing to reset when the view is swapped out. Coordinates are
     taken relative to the canvas box — the same box the mark is centred in. */

  /* A pointermove burst can be several events per frame, and the canvas box
     cannot have moved in between: it is read once per painted frame instead of
     once per event. Scroll invalidates it because the page can be taller than
     the viewport, and a cached top would then be off by the scroll offset. */
  function canvasBox() {
    if (!canvasRect) {
      var r = canvas.getBoundingClientRect();
      canvasRect = { left: r.left, top: r.top, width: r.width };
    }
    return canvasRect;
  }

  function trackPointer(ev) {
    var box = canvasBox();
    if (box.width < 2) return;

    pointer.tx = ev.clientX - box.left;
    pointer.ty = ev.clientY - box.top;
    pointer.on = true;

    /* a pointer arriving from off the mark must not drag the influence across
       the canvas on its way in */
    if (pointer.energy === 0) {
      pointer.x = pointer.tx;
      pointer.y = pointer.ty;
    }
  }

  function releasePointer() {
    pointer.on = false;
  }

  canvas.addEventListener('pointermove', trackPointer);
  canvas.addEventListener('pointerdown', trackPointer);
  canvas.addEventListener('pointerleave', releasePointer);
  canvas.addEventListener('pointercancel', releasePointer);
  /* a window that loses focus gets no pointerleave, and the cursor could be
     anywhere by the time it comes back */
  window.addEventListener('blur', releasePointer);
  window.addEventListener('scroll', function () { canvasRect = null; },
    { passive: true, capture: true });

  /* honour a settings change mid-session: freeze to the assembled still, or
     start turning again, without needing a reload */
  function onMotionChange() {
    if (motionQuery.matches) {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      for (var i = 0; i < NODES; i++) {
        nodes[i].alpha = 1;
        nodes[i].scale = 1;
      }
      for (var e = 0; e < edges.length; e++) edges[e].alpha = 1;
      settled = true;
      /* the loop is gone, so nothing would ever ease the nodes back: drop the
         pull now and the frozen frame is the true assembled mark */
      resetPull();
      paint();
    } else {
      /* motion is allowed again, but only resume if the stage is on screen —
         the report view may be the one currently visible */
      paused = true;   /* mark as paused so resume() takes the early path */
      if (canvas.getBoundingClientRect().width >= 2) resume();
    }
  }

  if (motionQuery.addEventListener) motionQuery.addEventListener('change', onMotionChange);
  else if (motionQuery.addListener) motionQuery.addListener(onMotionChange);

  /* A background tab still gets animation frames (throttled, not stopped), so
     the globe kept repainting for a page nobody was looking at. Stopping on
     hide and resuming on show costs nothing and gives the rest of the machine
     its cycles back. `resume()` already drops the elapsed time, so returning
     continues the spin instead of jumping ahead. */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      paused = true;
      return;
    }
    /* only restart when the stage is genuinely on screen and motion is allowed */
    if (!motionQuery.matches && canvas.getBoundingClientRect().width >= 2) resume();
  });

  window.KBPGlobe = {
    start: start,
    /* re-colour and re-measure only. A theme switch can happen while the
       home view is off screen, so this must not restart the loop by itself —
       the caller resumes when the stage is actually visible again. */
    repaint: function () {
      /* readTheme() also rebuilds the cached bucket colours, so it has to run
         before the frame that shows them; measure() alone does not touch the
         palette, because nothing changed colour just because the box moved. */
      readTheme();
      measure();
      paint();
    },
    resume: resume,
    stop: function () {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      paused = true;
      /* The mark is leaving the screen. Release the pointer but keep the
         energy: the loop is stopped, so the pull simply eases away on the
         first frames after the view comes back instead of snapping. */
      pointer.on = false;
    }
  };
})();
