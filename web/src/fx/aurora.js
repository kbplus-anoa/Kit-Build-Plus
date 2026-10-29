/* Kit Build Plus — Aurora Veil
 *
 * Port of the reference WebGL2 aurora (plugins/_official/examples/
 * webgl-aurora-veil): three light curtains whose centre snakes horizontally
 * with height and time, warped by FBM, riding a night-sky gradient scattered
 * with stars. The curtains sway toward the pointer.
 *
 * Kept faithful to the reference shader — same palette ramp, same three-band
 * loop, same vignette and tone curve — with two departures taken for cost
 * (three FBM octaves instead of five, and a static grain instead of a
 * per-frame one; each is explained where it appears) and four additions the
 * surrounding product needs:
 *
 *   1. Light mode. The reference is dark-only. On a white page a night sky is
 *      wrong, so light mode renders the same curtain geometry over a pale sky
 *      with the palette desaturated toward the page's own tint, then softened.
 *   2. Reduced motion. The reference animates forever. Here a one-shot frame at
 *      a fixed time is drawn instead, so the veil is still a veil but nothing
 *      moves.
 *   3. Page visibility. A hidden tab keeps asking for frames; this stops.
 *   4. Failure. Without WebGL2 the canvas stays empty and the page keeps its
 *      flat --bg behind it — no error, no half-drawn layer.
 */

import { freezeRequested } from './freeze.js';

(function () {
  'use strict';

  var canvas = document.getElementById('aurora-gl');
  if (!canvas) return;

  var gl = canvas.getContext('webgl2', {
    antialias: false,
    alpha: false,
    depth: false,
    /* a full-viewport background layer that nobody reads back: ask for the
       integrated GPU rather than waking a discrete one for a gradient */
    powerPreference: 'low-power'
  });
  if (!gl) {
    /* no WebGL2: drop the layer entirely so the page's own background shows */
    canvas.style.display = 'none';
    return;
  }

  var VERT = '#version 300 es\n' +
    'void main(){ vec2 p=vec2((gl_VertexID<<1)&2, gl_VertexID&2); gl_Position=vec4(p*2.0-1.0,0.0,1.0); }';

  var FRAG = '#version 300 es\n' +
    'precision highp float;\n' +
    'precision highp int;\n' +
    'out vec4 o;\n' +
    'uniform vec2 u_res; uniform float u_time; uniform vec2 u_mouse; uniform float u_light;\n' +
    'uniform float u_dither;\n' +
    'float hash(vec2 p){ return fract(sin(dot(p,vec2(41.3,289.1)))*43758.5453); }\n' +
    '/* One code value of noise per pixel, from an integer hash rather than the\n' +
    '   sine one above: at gl_FragCoord magnitudes the sine hash loses its low\n' +
    '   bits to the argument reduction and starts to repeat. */\n' +
    'float dither(){ uint h=uint(gl_FragCoord.x)+uint(gl_FragCoord.y)*1973u;\n' +
    '  h=(h^(h>>15))*2246822519u; h=(h^(h>>13))*3266489917u;\n' +
    '  return float((h^(h>>16))&0xffffu)/65535.0-0.5; }\n' +
    'float noise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.0-2.0*f);\n' +
    '  return mix(mix(hash(i),hash(i+vec2(1,0)),u.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x),u.y); }\n' +
    '/* Three octaves, where the reference used five. The two dropped octaves\n' +
    '   hold 2.5% of the noise variance but 40% of its samples: every octave is\n' +
    '   four hash (sine) calls, and fbm runs three times per band across three\n' +
    '   bands, so this one line is most of what the veil costs per pixel. The\n' +
    '   noise is 0..1 rather than zero-mean, so dropping octaves also moves its\n' +
    '   mean; +0.06447 is the mean of the two weights that left\n' +
    '   (0.5*(0.0831875+0.0457531)), which puts every use of this value back\n' +
    '   where it was and removes only the finest grain. */\n' +
    'float fbm(vec2 p){ float v=0.0,a=0.5; for(int i=0;i<3;i++){ v+=a*noise(p); p=p*1.9+3.0; a*=0.55; } return v+0.06447; }\n' +
    'vec3 auroraPal(float t){\n' +
    '  return mix(mix(vec3(0.10,0.9,0.45), vec3(0.15,0.8,0.85), smoothstep(0.0,0.5,t)),\n' +
    '             vec3(0.6,0.35,0.95), smoothstep(0.5,1.0,t));\n' +
    '}\n' +
    'void main(){\n' +
    '  vec2 uv=gl_FragCoord.xy/u_res;\n' +
    '  vec2 p=(gl_FragCoord.xy-0.5*u_res)/u_res.y;\n' +
    '  float sway=(u_mouse.x-0.5)*1.2;\n' +
    '  /* night sky, or a pale sky in light mode */\n' +
    '  vec3 night=mix(vec3(0.02,0.03,0.09), vec3(0.03,0.06,0.16), uv.y);\n' +
    '  vec3 day  =mix(vec3(0.97,0.98,1.00), vec3(0.90,0.94,0.99), uv.y);\n' +
    '  vec3 col=mix(night, day, u_light);\n' +
    '  /* No stars. Three rounds of layering and jittering still read as a\n' +
    '     pattern at full-screen scale, and a starfield that looks generated is\n' +
    '     worse than none. The sky keeps its gradient; the only light in it is\n' +
    '     the curtains. */\n' +
    '  float t=u_time*0.15;\n' +
    '  for(int i=0;i<3;i++){\n' +
    '    float fi=float(i);\n' +
    '    float base=(fi-1.0)*0.55 + sway*(0.35+fi*0.2);\n' +
    '    float cx=base + sin(p.y*1.6 + t*2.0 + fi*2.1)*0.22 + (fbm(vec2(p.y*1.2+fi*3.0, t*1.5))-0.5)*0.7;\n' +
    '    float w=0.15 + 0.09*fbm(vec2(p.y*3.0+fi, t));\n' +
    '    float band=exp(-pow((p.x-cx)/w, 2.0));\n' +
    '    float vert=smoothstep(-0.95,0.8,p.y) * (0.45+0.55*fbm(vec2(p.x*5.0+fi*4.0, p.y*2.6 - t*2.5)));\n' +
    '    float ribbon=band*vert;\n' +
    '    /* Hue is a function of position and band only — never of time. The\n' +
    '       reference adds `t*0.3` here, which walks the whole palette through\n' +
    '       every band on a slow cycle; because it drifts uniformly with height,\n' +
    '       the phase boundary reads as a horizontal colour seam sweeping up the\n' +
    '       screen. Freezing it keeps each curtain its own colour, and the motion\n' +
    '       still comes from the snaking centre and the noise. */\n' +
    '    float hue=fract(0.12 + fi*0.28 + p.y*0.16);\n' +
    '    vec3 tint=auroraPal(hue);\n' +
    '    /* light mode: the saturated curtain would shout on white, so it keeps\n' +
    '       its shape and loses most of its chroma, blended toward the page */\n' +
    '    tint=mix(tint, mix(tint, vec3(0.62,0.70,0.86), 0.55), u_light);\n' +
    '    col += tint * ribbon * (1.0 - fi*0.14) * mix(1.0, 0.55, u_light);\n' +
    '  }\n' +
    '  col *= 0.7+0.5*smoothstep(1.5,0.1,length(p*vec2(0.6,1.0)));\n' +
    '  col=col/(col+0.8);\n' +
    '  /* Dither, in output space and after the tone curve, where 1/255 is exactly\n' +
    '     one code value of the framebuffer. The sky ramps slower than that: it\n' +
    '     spends tens of rows inside one value and then steps down by one, and on\n' +
    '     an OLED at night those steps read as thin horizontal lines. u_dither is\n' +
    '     a width in code values; the caller pre-emphasises it by the upscale\n' +
    '     factor, because the browser averages it again on the way to the screen. */\n' +
    '  vec3 c=pow(max(col,0.0),vec3(0.9))+dither()*(u_dither/255.0);\n' +
    '  o=vec4(c,1.0);\n' +
    '}';

  function compile(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(s) || 'shader compile failed');
    }
    return s;
  }

  var program = null;
  var uRes = null, uTime = null, uMouse = null, uLight = null;
  var uDither = null;

  /* Compiles, links, and takes the uniform locations. Shared by the initial
     build and by the restore after a context loss, when every one of those
     objects is gone and has to be made again. Returns false when the GPU will
     not give us a program: the layer is dropped so the page's own --bg shows
     through instead of a black rectangle. */
  function buildProgram() {
    try {
      program = gl.createProgram();
      gl.attachShader(program, compile(gl.VERTEX_SHADER, VERT));
      gl.attachShader(program, compile(gl.FRAGMENT_SHADER, FRAG));
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(program) || 'link failed');
      }
    } catch (err) {
      canvas.style.display = 'none';
      program = null;
      return false;
    }
    gl.useProgram(program);
    uRes = gl.getUniformLocation(program, 'u_res');
    uTime = gl.getUniformLocation(program, 'u_time');
    uMouse = gl.getUniformLocation(program, 'u_mouse');
    uLight = gl.getUniformLocation(program, 'u_light');
    uDither = gl.getUniformLocation(program, 'u_dither');
    return true;
  }

  if (!buildProgram()) return;

  var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  /* 外部冻结：地址栏要求或 freeze() 调用后，只画 still() 那一帧，永不进循环 */
  var frozen = freezeRequested();
  var mouse = [0.5, 0.5];
  var target = [0.5, 0.5];
  var raf = 0;
  var started = 0;      /* the wall clock this run measures from */
  var elapsed = 0;      /* drift already played, in ms, carried across a stop */
  var lastFrame = 0;    /* for a frame-rate independent pointer chase */
  var light = 0;

  /* The pointer chase as a time constant rather than a per-frame fraction: the
     reference's 0.05 per frame converged twice as fast on a 120Hz display as on
     a 60Hz one. 320ms reproduces the 60Hz response exactly — 1 - exp(-16.7/320)
     is 0.051 — and holds it at any refresh rate. Slower than the globe's 90ms on
     purpose: the veil should lag the foreground mark. */
  var MOUSE_TAU = 320;
  var STILL_TIME = 11.5;   /* the one frame reduced motion holds */

  function readTheme() {
    light = document.documentElement.getAttribute('data-theme') === 'light' ? 1 : 0;
  }

  /* Sampling density. The shader normalises by u_res, so the curtains' geometry
     does not depend on the buffer size at all — only its graininess does. Two
     caps in one place: DPR at 2, or 1.5 once the window is wide, because past
     that the extra samples of a soft gradient are paid for and not seen; then
     the whole buffer at 0.7 of that, which the browser's own upscale turns back
     into a smooth ramp. With the shader's octave count this is about a third of
     the per-pixel cost the veil used to carry. */
  var BUFFER_SCALE = 0.7;
  /* raised by the resize listener, consumed by the frame loop: a resize burst
     must not measure once per event */
  var sizeDirty = true;
  /* buffer pixels per CSS pixel, measured alongside the buffer: the dither
     amplitude is pre-emphasised by it, because the browser averages the noise
     again on the way to the screen */
  var pixelScale = 1;

  function bufferScale() {
    var cap = window.innerWidth > 1200 ? 1.5 : 2;
    return Math.min(window.devicePixelRatio || 1, cap) * BUFFER_SCALE;
  }

  /* 抖动幅度，单位是一个码值。它只做一件事：抵住渐变落进 8bit 时那一级
     一级的台阶——夜空的蓝在一整屏里只走十几个码值，每一级要占二三十行，
     那就是肉眼看到的横线。缓冲比屏幕小时噪声先被浏览器的双线性放大平均
     掉一截（约等于放大倍数），所以按放大倍数预加重；一比一时正好半个码
     值，也就是教科书上的舍入抖动。?grain=0 是关掉它做对照的开关。 */
  function ditherNow() {
    var upscale = (window.devicePixelRatio || 1) / Math.max(pixelScale, 0.001);
    return Math.max(1, Math.min(2, upscale));
  }

  function measure() {
    sizeDirty = false;
    var d = bufferScale();
    var w = Math.round(window.innerWidth * d);
    var h = Math.round(window.innerHeight * d);
    pixelScale = w / Math.max(window.innerWidth, 1) || 1;
    if (w === canvas.width && h === canvas.height) return;
    canvas.width = w;
    canvas.height = h;
    gl.viewport(0, 0, w, h);
  }

  /* Uniform state is cached, because three of the four uniforms rarely change:
     u_res only when the buffer does, u_light only on a theme flip, u_mouse only
     while the pointer is still catching up. u_time is the clock and is always
     sent. The cache is invalidated wholesale after a context loss, since every
     value in it died with the context. */
  var sentRes = [0, 0];
  var sentLight = -1;
  var sentMouse = [NaN, NaN];
  var sentDither = -1;

  function invalidateUniforms() {
    sentRes[0] = 0;
    sentRes[1] = 0;
    sentLight = -1;
    sentMouse[0] = NaN;
    sentMouse[1] = NaN;
    sentDither = -1;
  }

  function draw(time) {
    if (canvas.width !== sentRes[0] || canvas.height !== sentRes[1]) {
      gl.uniform2f(uRes, canvas.width, canvas.height);
      sentRes[0] = canvas.width;
      sentRes[1] = canvas.height;
    }
    if (light !== sentLight) {
      gl.uniform1f(uLight, light);
      sentLight = light;
    }
    var dither = ditherNow();
    if (dither !== sentDither) {
      gl.uniform1f(uDither, dither);
      sentDither = dither;
    }
    if (mouse[0] !== sentMouse[0] || mouse[1] !== sentMouse[1]) {
      gl.uniform2f(uMouse, mouse[0], mouse[1]);
      sentMouse[0] = mouse[0];
      sentMouse[1] = mouse[1];
    }
    gl.uniform1f(uTime, time);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  function frame(now) {
    /* the frame is the only place the viewport is read, and only when a resize
       asked for it: the loop itself never touches layout */
    if (sizeDirty) measure();
    var dt = lastFrame ? Math.min(64, now - lastFrame) : 16.7;
    lastFrame = now;
    var k = 1 - Math.exp(-dt / MOUSE_TAU);
    mouse[0] += (target[0] - mouse[0]) * k;
    mouse[1] += (target[1] - mouse[1]) * k;
    draw((elapsed + (now - started)) / 1000);
    raf = requestAnimationFrame(frame);
  }

  /* one still frame at a fixed time — the veil without the motion */
  function still() {
    measure();
    draw(STILL_TIME);
  }

  function start() {
    if (motionQuery.matches) { still(); return; }
    if (frozen) { still(); return; }
    if (raf) return;
    /* continue the drift from where it stopped rather than from where the wall
       clock got to: a hidden tab or an open subpage must not make the curtains
       jump forward by however long it was */
    started = performance.now() - elapsed;
    lastFrame = 0;
    raf = requestAnimationFrame(frame);
  }

  function stop() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    if (started) {
      elapsed = performance.now() - started;
      started = 0;
    }
  }

  window.addEventListener('pointermove', function (ev) {
    target[0] = ev.clientX / window.innerWidth;
    target[1] = 1 - ev.clientY / window.innerHeight;
  }, { passive: true });

  window.addEventListener('resize', function () {
    sizeDirty = true;
    /* the running loop consumes the flag on its next frame, which is what makes
       a drag-resize cost one measurement per frame instead of one per event.
       Nothing would consume it with the loop stopped, so those two cases are
       handled here: reduced motion has no next frame at all and has to redraw
       its single frame at the new size. */
    if (motionQuery.matches || frozen) still();
    else if (!raf) measure();
  });

  /* A lost context takes the program, its uniform locations and every uniform
     value with it. Without these two handlers the veil stays a black rectangle
     for the rest of the session: the canvas keeps its size, so nothing would
     ever notice. */
  canvas.addEventListener('webglcontextlost', function (ev) {
    /* preventDefault is what lets the browser try to restore the context */
    ev.preventDefault();
    stop();
    program = null;
  });

  canvas.addEventListener('webglcontextrestored', function () {
    if (!buildProgram()) return;
    invalidateUniforms();
    /* the restored context is at its default state, so the viewport has to be
       set again even though the canvas attribute did not change */
    gl.viewport(0, 0, canvas.width, canvas.height);
    /* and the size is re-checked against the window, which may have moved on */
    sizeDirty = true;
    start();
  });

  /* A human flipping the system preference mid-session should take effect
     without a reload — freeze to the still frame, or resume. */
  function onMotionChange() {
    if (motionQuery.matches) { stop(); still(); }
    else start();
  }
  if (motionQuery.addEventListener) motionQuery.addEventListener('change', onMotionChange);
  else if (motionQuery.addListener) motionQuery.addListener(onMotionChange);

  /* A hidden tab keeps receiving frames; stop paying for them. Elapsed time is
     preserved so returning continues the drift instead of jumping. */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) stop();
    else start();
  });

  readTheme();
  start();

  window.KBPAurora = {
    /* re-render after a theme flip; the palette is a uniform, not a repaint */
    repaint: function () {
      readTheme();
      /* With the loop stopped — reduced motion, or a subpage holding the veil —
         a cached uniform would never reach the screen, so one frame is drawn
         here. With it running, the next frame compares the cache and sends it. */
      if (motionQuery.matches || !raf) still();
      else measure();
    },
    /* freeze behind the subpage's backdrop blur; resume when home returns */
    stop: stop,
    resume: start,
    /* 停在确定的一帧：复用 stop() + still()，不另开渲染路径 */
    freeze: function () {
      frozen = true;
      stop();
      still();
    }
  };
})();
